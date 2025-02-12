from typing import Optional
import discord
from datetime import datetime, timedelta

class Punishment:
    """Класс для управления наказаниями"""
    def __init__(self, bot):
        self.bot = bot
        
    async def apply_punishment(self, member: discord.Member, punishment_type: str, reason: str) -> bool:
        """Применить наказание к участнику"""
        try:
            if punishment_type.startswith("warn"):
                await self.warn_member(member, reason)
            elif punishment_type.startswith("mute"):
                duration = self._parse_duration(punishment_type)
                await self.mute_member(member, duration, reason)
            elif punishment_type.startswith("ban"):
                duration = self._parse_duration(punishment_type)
                await self.ban_member(member, duration, reason)
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
            
    async def warn_member(self, member: discord.Member, reason: str):
        """Выдать предупреждение участнику"""
        # Здесь будет интеграция с системой предупреждений
        pass
        
    async def mute_member(self, member: discord.Member, duration: timedelta, reason: str):
        """Замутить участника"""
        try:
            # Получаем роль мута
            mute_role = discord.utils.get(member.guild.roles, name="Muted")
            if not mute_role:
                # Создаем роль мута если её нет
                mute_role = await member.guild.create_role(
                    name="Muted",
                    reason="Автоматически создана роль мута"
                )
                
                # Настраиваем права для роли
                for channel in member.guild.channels:
                    await channel.set_permissions(mute_role, send_messages=False, add_reactions=False)
                    
            await member.add_roles(mute_role, reason=reason)
            
            # Снимаем мут после истечения срока
            await self.schedule_unmute(member, duration)
            
        except Exception as e:
            print(f"Ошибка при муте участника: {e}")
            
    async def schedule_unmute(self, member: discord.Member, duration: timedelta):
        """Запланировать снятие мута"""
        await discord.utils.sleep_until(datetime.now() + duration)
        try:
            mute_role = discord.utils.get(member.guild.roles, name="Muted")
            if mute_role and mute_role in member.roles:
                await member.remove_roles(mute_role, reason="Истек срок мута")
        except Exception as e:
            print(f"Ошибка при снятии мута: {e}")
            
    async def ban_member(self, member: discord.Member, duration: timedelta, reason: str):
        """Забанить участника"""
        try:
            await member.ban(reason=reason)
            
            # Снимаем бан после истечения срока
            await self.schedule_unban(member, duration)
            
        except Exception as e:
            print(f"Ошибка при бане участника: {e}")
            
    async def schedule_unban(self, member: discord.Member, duration: timedelta):
        """Запланировать разбан"""
        await discord.utils.sleep_until(datetime.now() + duration)
        try:
            await member.guild.unban(member, reason="Истек срок бана")
        except Exception as e:
            print(f"Ошибка при разбане участника: {e}")
            
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