from typing import Dict, Optional, List
import discord
from ..utils.embed import Embed
from ..utils.constants import Emojis
from ..database.db import Database

class AutoModManager:
    """Менеджер автомодерации"""
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        
    async def get_violations(self, user_id: int, guild_id: int) -> Dict[str, int]:
        """Получить нарушения пользователя"""
        violations = await self.db.fetch_all(
            """
            SELECT rule_name, COUNT(*) as count
            FROM moderation 
            WHERE user_id = ? AND guild_id = ? AND type = 'violation' AND active = TRUE
            GROUP BY rule_name
            """,
            str(user_id), str(guild_id)
        )
        return {v['rule_name']: v['count'] for v in violations}
        
    async def clear_violations(self, user_id: int, guild_id: int) -> bool:
        """Очистить все нарушения пользователя"""
        try:
            await self.db.execute(
                """
                UPDATE moderation 
                SET active = FALSE 
                WHERE user_id = ? AND guild_id = ? AND type = 'violation'
                """,
                str(user_id), str(guild_id)
            )
            return True
        except Exception:
            return False
            
    async def get_channel_exceptions(self, channel_id: int) -> List[str]:
        """Получить список исключений для канала"""
        exceptions = await self.db.fetch_all(
            """
            SELECT rule_name 
            FROM automod_exceptions 
            WHERE channel_id = ?
            """,
            str(channel_id)
        )
        return [e['rule_name'] for e in exceptions]
        
    async def add_exception(self, channel_id: int, rule_name: str) -> bool:
        """Добавить исключение для канала"""
        try:
            # Проверяем, существует ли уже такое исключение
            existing = await self.db.fetch_one(
                """
                SELECT id FROM automod_exceptions 
                WHERE channel_id = ? AND rule_name = ?
                """,
                str(channel_id), rule_name.lower()
            )
            
            if existing:
                return True  # Исключение уже существует
                
            await self.db.execute(
                """
                INSERT INTO automod_exceptions (channel_id, rule_name)
                VALUES (?, ?)
                """,
                str(channel_id), rule_name.lower()
            )
            return True
        except Exception as e:
            print(f"Ошибка при добавлении исключения: {e}")
            return False
            
    async def remove_exception(self, channel_id: int, rule_name: str) -> bool:
        """Удалить исключение для канала"""
        try:
            await self.db.execute(
                """
                DELETE FROM automod_exceptions 
                WHERE channel_id = ? AND rule_name = ?
                """,
                str(channel_id), rule_name
            )
            return True
        except Exception as e:
            print(f"Ошибка при удалении исключения: {e}")
            return False
            
    def create_violations_embed(self, member: discord.Member, violations: Dict[str, int], rules: Dict[str, object]) -> Embed:
        """Создать эмбед с нарушениями пользователя"""
        if not violations:
            return Embed(
                title=f"{Emojis.INFO} История нарушений",
                description=f"У {member.mention} нет нарушений",
                color="BLUE"
            )
            
        embed = Embed(
            title=f"{Emojis.INFO} История нарушений",
            description=f"Нарушения {member.mention}:",
            color="BLUE"
        )
        
        for rule_name, count in violations.items():
            if rule_name in rules:
                rule = rules[rule_name]
                embed.add_field(
                    name=f"{Emojis.DOT} {rule.name}",
                    value=f"Количество: `{count}`\nПоследнее наказание: `{rule.punishment.get(count, 'warn')}`",
                    inline=False
                )
                
        return embed 