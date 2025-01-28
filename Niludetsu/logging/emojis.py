from ..core.base import BaseLogger, EMOJIS
import discord
from typing import Optional, List

class EmojiLogger(BaseLogger):
    """Логгер для событий, связанных с эмодзи Discord."""
    
    async def log_emoji_create(self, emoji: discord.Emoji):
        """Логирование создания эмодзи"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Название", "value": emoji.name, "inline": True},
            {"name": f"{EMOJIS['DOT']} ID", "value": str(emoji.id), "inline": True},
            {"name": f"{EMOJIS['DOT']} Анимированный", "value": "Да" if emoji.animated else "Нет", "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['SUCCESS']} Создан новый эмодзи",
            description=f"Добавлен эмодзи {emoji}",
            color='GREEN',
            fields=fields,
            thumbnail_url=emoji.url
        )
        
    async def log_emoji_delete(self, emoji: discord.Emoji):
        """Логирование удаления эмодзи"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Название", "value": emoji.name, "inline": True},
            {"name": f"{EMOJIS['DOT']} ID", "value": str(emoji.id), "inline": True},
            {"name": f"{EMOJIS['DOT']} Анимированный", "value": "Да" if emoji.animated else "Нет", "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['ERROR']} Эмодзи удален",
            description=f"Удален эмодзи :{emoji.name}:",
            color='RED',
            fields=fields,
            thumbnail_url=emoji.url
        )
        
    async def log_emoji_name_update(self, before: discord.Emoji, after: discord.Emoji):
        """Логирование изменения имени эмодзи"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Эмодзи", "value": str(after), "inline": True},
            {"name": f"{EMOJIS['DOT']} Старое имя", "value": before.name, "inline": True},
            {"name": f"{EMOJIS['DOT']} Новое имя", "value": after.name, "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['INFO']} Изменено имя эмодзи",
            description=f"Эмодзи {after} был переименован",
            color='BLUE',
            fields=fields,
            thumbnail_url=after.url
        )
        
    async def log_emoji_roles_update(self, emoji: discord.Emoji, before_roles: List[discord.Role], after_roles: List[discord.Role]):
        """Логирование изменения ролей эмодзи"""
        before_roles_text = ", ".join([role.mention for role in before_roles]) or "Все роли"
        after_roles_text = ", ".join([role.mention for role in after_roles]) or "Все роли"
        
        fields = [
            {"name": f"{EMOJIS['DOT']} Эмодзи", "value": str(emoji), "inline": True},
            {"name": f"{EMOJIS['DOT']} Старые роли", "value": before_roles_text, "inline": False},
            {"name": f"{EMOJIS['DOT']} Новые роли", "value": after_roles_text, "inline": False}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['INFO']} Изменены роли эмодзи",
            description=f"Обновлены роли для эмодзи {emoji}",
            color='BLUE',
            fields=fields,
            thumbnail_url=emoji.url
        )
        
    async def log_emoji_update(self, before: discord.Emoji, after: discord.Emoji):
        """Общий метод для логирования изменений эмодзи"""
        if before.name != after.name:
            await self.log_emoji_name_update(before, after)
        if set(before.roles) != set(after.roles):
            await self.log_emoji_roles_update(after, list(before.roles), list(after.roles)) 