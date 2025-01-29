from ..utils.logging import BaseLogger
from ..utils.emojis import EMOJIS
import discord
from typing import Optional

class StickerLogger(BaseLogger):
    """Логгер для стикеров Discord."""
    
    async def log_sticker_create(self, sticker: discord.GuildSticker):
        """Логирование создания стикера"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Название", "value": sticker.name, "inline": True},
            {"name": f"{EMOJIS['DOT']} ID", "value": str(sticker.id), "inline": True},
            {"name": f"{EMOJIS['DOT']} Эмодзи", "value": sticker.emoji or "Не указан", "inline": True},
            {"name": f"{EMOJIS['DOT']} Формат", "value": str(sticker.format), "inline": True},
            {"name": f"{EMOJIS['DOT']} Описание", "value": sticker.description or "Отсутствует", "inline": False}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['SUCCESS']} Создан новый стикер",
            description=f"На сервер добавлен новый стикер",
            color='GREEN',
            fields=fields,
            thumbnail_url=sticker.url
        )
        
    async def log_sticker_delete(self, sticker: discord.GuildSticker):
        """Логирование удаления стикера"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Название", "value": sticker.name, "inline": True},
            {"name": f"{EMOJIS['DOT']} ID", "value": str(sticker.id), "inline": True},
            {"name": f"{EMOJIS['DOT']} Эмодзи", "value": sticker.emoji or "Не указан", "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['ERROR']} Стикер удален",
            description=f"С сервера удален стикер",
            color='RED',
            fields=fields,
            thumbnail_url=sticker.url
        )
        
    async def log_sticker_name_update(self, before: discord.GuildSticker, after: discord.GuildSticker):
        """Логирование изменения названия стикера"""
        fields = [
            {"name": f"{EMOJIS['DOT']} ID", "value": str(after.id), "inline": True},
            {"name": f"{EMOJIS['DOT']} Старое название", "value": before.name, "inline": True},
            {"name": f"{EMOJIS['DOT']} Новое название", "value": after.name, "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['INFO']} Изменено название стикера",
            description=f"Обновлено название стикера",
            color='BLUE',
            fields=fields,
            thumbnail_url=after.url
        )
        
    async def log_sticker_description_update(self, before: discord.GuildSticker, after: discord.GuildSticker):
        """Логирование изменения описания стикера"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Название", "value": after.name, "inline": True},
            {"name": f"{EMOJIS['DOT']} Старое описание", "value": before.description or "Отсутствует", "inline": False},
            {"name": f"{EMOJIS['DOT']} Новое описание", "value": after.description or "Отсутствует", "inline": False}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['INFO']} Изменено описание стикера",
            description=f"Обновлено описание стикера",
            color='BLUE',
            fields=fields,
            thumbnail_url=after.url
        )
        
    async def log_sticker_emoji_update(self, before: discord.GuildSticker, after: discord.GuildSticker):
        """Логирование изменения связанного эмодзи стикера"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Название", "value": after.name, "inline": True},
            {"name": f"{EMOJIS['DOT']} Старый эмодзи", "value": before.emoji or "Отсутствует", "inline": True},
            {"name": f"{EMOJIS['DOT']} Новый эмодзи", "value": after.emoji or "Отсутствует", "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['INFO']} Изменен эмодзи стикера",
            description=f"Обновлен связанный эмодзи стикера",
            color='BLUE',
            fields=fields,
            thumbnail_url=after.url
        ) 