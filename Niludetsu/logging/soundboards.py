from ..utils.logging import BaseLogger
from ..utils.constants import Emojis
import discord
from typing import Optional, Dict, Any

class SoundboardSound:
    """Класс для представления звука в Soundboard."""
    def __init__(self, **kwargs):
        self.id: int = kwargs.get('id')
        self.name: str = kwargs.get('name')
        self.emoji: Optional[str] = kwargs.get('emoji')
        self.volume: int = kwargs.get('volume', 100)
        self.user: Optional[discord.Member] = kwargs.get('user')
        self.guild: Optional[discord.Guild] = kwargs.get('guild')

class SoundboardLogger(BaseLogger):
    """Логгер для звуков Soundboard Discord."""
    
    async def log_soundboard_create(self, data: Dict[str, Any]):
        """Логирование загрузки звука"""
        fields = [
            {"name": f"{Emojis.DOT} Название", "value": data.get('name', 'Неизвестно'), "inline": True},
            {"name": f"{Emojis.DOT} ID", "value": str(data.get('id', 'Неизвестно')), "inline": True},
            {"name": f"{Emojis.DOT} Эмодзи", "value": data.get('emoji', 'Не указан'), "inline": True},
            {"name": f"{Emojis.DOT} Громкость", "value": f"{data.get('volume', 100)}%", "inline": True},
            {"name": f"{Emojis.DOT} Пользователь", "value": str(data.get('user', 'Неизвестно')), "inline": True}
        ]
        
        await self.log_event(
            title=f"{Emojis.SUCCESS} Загружен новый звук",
            description=f"В Soundboard добавлен новый звук",
            color='GREEN',
            fields=fields
        )
        
    async def log_soundboard_delete(self, data: Dict[str, Any]):
        """Логирование удаления звука"""
        fields = [
            {"name": f"{Emojis.DOT} Название", "value": data.get('name', 'Неизвестно'), "inline": True},
            {"name": f"{Emojis.DOT} ID", "value": str(data.get('id', 'Неизвестно')), "inline": True},
            {"name": f"{Emojis.DOT} Эмодзи", "value": data.get('emoji', 'Не указан'), "inline": True}
        ]
        
        await self.log_event(
            title=f"{Emojis.ERROR} Звук удален",
            description=f"Из Soundboard удален звук",
            color='RED',
            fields=fields
        )
        
    async def log_soundboard_name_update(self, before: Dict[str, Any], after: Dict[str, Any]):
        """Логирование изменения названия звука"""
        fields = [
            {"name": f"{Emojis.DOT} ID", "value": str(after.get('id', 'Неизвестно')), "inline": True},
            {"name": f"{Emojis.DOT} Старое название", "value": before.get('name', 'Неизвестно'), "inline": True},
            {"name": f"{Emojis.DOT} Новое название", "value": after.get('name', 'Неизвестно'), "inline": True}
        ]
        
        await self.log_event(
            title=f"{Emojis.INFO} Изменено название звука",
            description=f"Обновлено название звука в Soundboard",
            color='BLUE',
            fields=fields
        )
        
    async def log_soundboard_volume_update(self, before: Dict[str, Any], after: Dict[str, Any]):
        """Логирование изменения громкости звука"""
        fields = [
            {"name": f"{Emojis.DOT} Название", "value": after.get('name', 'Неизвестно'), "inline": True},
            {"name": f"{Emojis.DOT} Старая громкость", "value": f"{before.get('volume', 100)}%", "inline": True},
            {"name": f"{Emojis.DOT} Новая громкость", "value": f"{after.get('volume', 100)}%", "inline": True}
        ]
        
        await self.log_event(
            title=f"{Emojis.INFO} Изменена громкость звука",
            description=f"Обновлена громкость звука в Soundboard",
            color='BLUE',
            fields=fields
        )
        
    async def log_soundboard_emoji_update(self, before: Dict[str, Any], after: Dict[str, Any]):
        """Логирование изменения эмодзи звука"""
        fields = [
            {"name": f"{Emojis.DOT} Название", "value": after.get('name', 'Неизвестно'), "inline": True},
            {"name": f"{Emojis.DOT} Старый эмодзи", "value": before.get('emoji', 'Отсутствует'), "inline": True},
            {"name": f"{Emojis.DOT} Новый эмодзи", "value": after.get('emoji', 'Отсутствует'), "inline": True}
        ]
        
        await self.log_event(
            title=f"{Emojis.INFO} Изменен эмодзи звука",
            description=f"Обновлен эмодзи звука в Soundboard",
            color='BLUE',
            fields=fields
        )