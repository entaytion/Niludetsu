from Niludetsu import BaseLogger, Emojis, LoggingState
import discord
from typing import Optional, List

class EmojiLogger(BaseLogger):
    """Логгер для событий, связанных с эмодзи Discord."""
    
    def __init__(self, bot: discord.Client):
        super().__init__(bot)
        self.log_channel = None
        bot.loop.create_task(self._initialize())
    
    async def _initialize(self):
        """Инициализация логгера"""
        await self.bot.wait_until_ready()
        await self.initialize_logs()
        self.log_channel = LoggingState.log_channel
        
    async def log_emoji_create(self, emoji: discord.Emoji):
        """Логирование создания эмодзи"""
        fields = [
            {"name": f"{Emojis.DOT} Название", "value": emoji.name, "inline": True},
            {"name": f"{Emojis.DOT} ID", "value": str(emoji.id), "inline": True},
            {"name": f"{Emojis.DOT} Анимированный", "value": "Да" if emoji.animated else "Нет", "inline": True}
        ]
        
        await self.log_event(
            title=f"{Emojis.SUCCESS} Создан новый эмодзи",
            description=f"Добавлен эмодзи {emoji}",
            color='GREEN',
            fields=fields,
            thumbnail_url=emoji.url
        )
        
    async def log_emoji_delete(self, emoji: discord.Emoji):
        """Логирование удаления эмодзи"""
        fields = [
            {"name": f"{Emojis.DOT} Название", "value": emoji.name, "inline": True},
            {"name": f"{Emojis.DOT} ID", "value": str(emoji.id), "inline": True},
            {"name": f"{Emojis.DOT} Анимированный", "value": "Да" if emoji.animated else "Нет", "inline": True}
        ]
        
        await self.log_event(
            title=f"{Emojis.ERROR} Эмодзи удален",
            description=f"Удален эмодзи :{emoji.name}:",
            color='RED',
            fields=fields,
            thumbnail_url=emoji.url
        )
        
    async def log_emoji_name_update(self, before: discord.Emoji, after: discord.Emoji):
        """Логирование изменения имени эмодзи"""
        fields = [
            {"name": f"{Emojis.DOT} Эмодзи", "value": str(after), "inline": True},
            {"name": f"{Emojis.DOT} Старое имя", "value": before.name, "inline": True},
            {"name": f"{Emojis.DOT} Новое имя", "value": after.name, "inline": True}
        ]
        
        await self.log_event(
            title=f"{Emojis.INFO} Изменено имя эмодзи",
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
            {"name": f"{Emojis.DOT} Эмодзи", "value": str(emoji), "inline": True},
            {"name": f"{Emojis.DOT} Старые роли", "value": before_roles_text, "inline": False},
            {"name": f"{Emojis.DOT} Новые роли", "value": after_roles_text, "inline": False}
        ]
        
        await self.log_event(
            title=f"{Emojis.INFO} Изменены роли эмодзи",
            description=f"Обновлены роли для эмодзи {emoji}",
            color='BLUE',
            fields=fields,
            thumbnail_url=emoji.url
        )
        
    async def log_emoji_update(self, before: tuple[discord.Emoji, ...], after: tuple[discord.Emoji, ...]):
        """Общий метод для логирования изменений эмодзи"""
        # Создаем словари для быстрого поиска эмодзи по ID
        before_emojis = {e.id: e for e in before}
        after_emojis = {e.id: e for e in after}
        
        # Проверяем удаленные эмодзи
        for emoji_id in before_emojis:
            if emoji_id not in after_emojis:
                await self.log_emoji_delete(before_emojis[emoji_id])
        
        # Проверяем новые эмодзи
        for emoji_id in after_emojis:
            if emoji_id not in before_emojis:
                await self.log_emoji_create(after_emojis[emoji_id])
        
        # Проверяем измененные эмодзи
        for emoji_id in after_emojis:
            if emoji_id in before_emojis:
                before_emoji = before_emojis[emoji_id]
                after_emoji = after_emojis[emoji_id]
                
                if before_emoji.name != after_emoji.name:
                    await self.log_emoji_name_update(before_emoji, after_emoji)
                if set(before_emoji.roles) != set(after_emoji.roles):
                    await self.log_emoji_roles_update(after_emoji, list(before_emoji.roles), list(after_emoji.roles)) 