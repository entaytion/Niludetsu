from typing import Optional
import discord
from datetime import datetime, timedelta
from Niludetsu.database.db import Database
import yaml

class Punishment:
    """Класс для управления наказаниями"""
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        # Загружаем ID роли мута из конфига
        try:
            with open('data/config.yaml', 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                self.muted_role_id = int(config.get('roles', {}).get('special', {}).get('muted', {}).get('id', 0))
        except Exception as e:
            print(f"❌ Ошибка при загрузке ID роли мута: {e}")
            self.muted_role_id = 0
        
    async def apply_punishment(self, member: discord.Member, punishment_type: str, reason: str, rule_name: Optional[str] = None, moderator_id: Optional[str] = None) -> bool:
        """Применить наказание к участнику"""
        try:
            # Определяем тип и длительность наказания
            if punishment_type.startswith("warn"):
                await self.warn_member(member, reason, rule_name, moderator_id)
            elif punishment_type.startswith("mute"):
                duration = self._parse_duration(punishment_type)
                await self.mute_member(member, duration, reason, rule_name, moderator_id)
            elif punishment_type.startswith("ban"):
                duration = self._parse_duration(punishment_type)
                await self.ban_member(member, duration, reason, rule_name, moderator_id)
            return True
        except Exception as e:
            print(f"Ошибка при применении наказания: {e}")
            return False
            
    def _parse_duration(self, punishment_type: str) -> timedelta:
        """Парсинг длительности наказания"""
        parts = punishment_type.split('_')
        if len(parts) != 2:
            return timedelta(hours=1)  # Значение по умолчанию
            
        value = int(parts[1][:-1])  # Убираем последнюю букву (h/d)
        unit = parts[1][-1]  # Получаем единицу измерения (h/d)
        
        if unit == 'h':
            return timedelta(hours=value)
        elif unit == 'd':
            return timedelta(days=value)
        else:
            return timedelta(hours=1)
            
    async def warn_member(self, member: discord.Member, reason: str, rule_name: Optional[str] = None, moderator_id: Optional[str] = None):
        """Выдать предупреждение участнику"""
        await self.db.execute(
            """
            INSERT INTO moderation (
                user_id, guild_id, moderator_id, type, rule_name, 
                reason, created_at, active
            ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, TRUE)
            """,
            str(member.id), str(member.guild.id), str(moderator_id), 
            "warn", rule_name, reason
        )
        
    async def mute_member(self, member: discord.Member, duration: timedelta, reason: str, rule_name: Optional[str] = None, moderator_id: Optional[str] = None):
        """Замутить участника"""
        try:
            # Используем существующую роль мута
            if not self.muted_role_id:
                print("❌ ID роли мута не настроен в конфиге")
                return False
                
            mute_role = member.guild.get_role(self.muted_role_id)
            if not mute_role:
                print(f"❌ Роль мута с ID {self.muted_role_id} не найдена")
                return False
                    
            await member.add_roles(mute_role, reason=reason)
            
            # Записываем в базу
            expires_at = datetime.now() + duration
            await self.db.execute(
                """
                INSERT INTO moderation (
                    user_id, guild_id, moderator_id, type, rule_name,
                    reason, created_at, expires_at, active
                ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, TRUE)
                """,
                str(member.id), str(member.guild.id), str(moderator_id),
                "mute", rule_name, reason, expires_at
            )
            
            # Снимаем мут после истечения срока
            await self.schedule_unmute(member, duration)
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при муте участника: {e}")
            return False
            
    async def schedule_unmute(self, member: discord.Member, duration: timedelta):
        """Запланировать снятие мута"""
        await discord.utils.sleep_until(datetime.now() + duration)
        try:
            if not self.muted_role_id:
                return
                
            mute_role = member.guild.get_role(self.muted_role_id)
            if mute_role and mute_role in member.roles:
                await member.remove_roles(mute_role, reason="Истек срок мута")
                
                # Обновляем статус в базе
                await self.db.execute(
                    """
                    UPDATE moderation 
                    SET active = FALSE 
                    WHERE user_id = ? AND guild_id = ? AND type = 'mute' AND active = TRUE
                    """,
                    str(member.id), str(member.guild.id)
                )
        except Exception as e:
            print(f"❌ Ошибка при снятии мута: {e}")
            
    async def ban_member(self, member: discord.Member, duration: timedelta, reason: str, rule_name: Optional[str] = None, moderator_id: Optional[str] = None):
        """Забанить участника"""
        try:
            await member.ban(reason=reason)
            
            # Записываем в базу
            expires_at = datetime.now() + duration if duration else None
            await self.db.execute(
                """
                INSERT INTO moderation (
                    user_id, guild_id, moderator_id, type, rule_name,
                    reason, created_at, expires_at, active
                ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, TRUE)
                """,
                str(member.id), str(member.guild.id), str(moderator_id),
                "ban", rule_name, reason, expires_at
            )
            
            # Снимаем бан после истечения срока
            if duration:
                await self.schedule_unban(member, duration)
            
        except Exception as e:
            print(f"Ошибка при бане участника: {e}")
            
    async def schedule_unban(self, member: discord.Member, duration: timedelta):
        """Запланировать разбан"""
        await discord.utils.sleep_until(datetime.now() + duration)
        try:
            await member.guild.unban(member, reason="Истек срок бана")
            
            # Обновляем статус в базе
            await self.db.execute(
                """
                UPDATE moderation 
                SET active = FALSE 
                WHERE user_id = ? AND guild_id = ? AND type = 'ban' AND active = TRUE
                """,
                str(member.id), str(member.guild.id)
            )
        except Exception as e:
            print(f"Ошибка при разбане участника: {e}")
            
    async def get_user_punishments(self, user_id: int, guild_id: int) -> list:
        """Получить историю наказаний пользователя"""
        return await self.db.fetch_all(
            """
            SELECT * FROM moderation 
            WHERE user_id = ? AND guild_id = ? 
            AND type IN ('warn', 'mute', 'ban')
            ORDER BY created_at DESC
            """,
            str(user_id), str(guild_id)
        )
            
    async def get_punishment_embed(self, member: discord.Member, rule_name: str, punishment_type: str, reason: str) -> discord.Embed:
        """Создать эмбед с информацией о наказании"""
        from Niludetsu.utils.embed import Embed
        from Niludetsu.utils.constants import Emojis
        
        punishment_names = {
            "warn": "Предупреждение",
            "mute": "Мут",
            "ban": "Бан"
        }
        
        punishment_base = punishment_type.split('_')[0]
        punishment_name = punishment_names.get(punishment_base, "Наказание")
        
        duration = self._parse_duration(punishment_type) if '_' in punishment_type else None
        duration_text = f" на {duration.days}д {duration.seconds//3600}ч" if duration else ""
        
        embed = Embed(
            title=f"{Emojis.ERROR} {punishment_name}",
            description=f"{Emojis.DOT} **Участник:** {member.mention}\n"
                      f"{Emojis.DOT} **Причина:** {rule_name} - {reason}\n"
                      f"{Emojis.DOT} **Длительность:** {duration_text if duration else 'Бессрочно'}",
            color="RED"
        )
        
        return embed 