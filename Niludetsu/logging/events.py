from Niludetsu import BaseLogger, Emojis, LoggingState
import discord
from typing import Optional, List
from discord import ScheduledEvent

class EventLogger(BaseLogger):
    """Логгер для событий Discord."""
    
    def __init__(self, bot: discord.Client):
        super().__init__(bot)
        self.log_channel = None
        bot.loop.create_task(self._initialize())
    
    async def _initialize(self):
        """Инициализация логгера"""
        await self.bot.wait_until_ready()
        await self.initialize_logs()
        self.log_channel = LoggingState.log_channel
        
    async def log_event_create(self, event: ScheduledEvent):
        """Логирование создания события"""
        fields = [
            {"name": f"{Emojis.DOT} Название", "value": event.name, "inline": True},
            {"name": f"{Emojis.DOT} ID", "value": str(event.id), "inline": True},
            {"name": f"{Emojis.DOT} Создатель", "value": event.creator.mention if event.creator else "Неизвестно", "inline": True},
            {"name": f"{Emojis.DOT} Начало", "value": discord.utils.format_dt(event.start_time), "inline": True},
            {"name": f"{Emojis.DOT} Конец", "value": discord.utils.format_dt(event.end_time) if event.end_time else "Не указано", "inline": True},
            {"name": f"{Emojis.DOT} Описание", "value": event.description or "Нет описания", "inline": False}
        ]
        
        await self.log_event(
            title=f"{Emojis.SUCCESS} Создано новое событие",
            description=f"Создано новое событие сервера",
            color='GREEN',
            fields=fields,
            thumbnail_url=event.cover.url if event.cover else None
        )
        
    async def log_event_delete(self, event: ScheduledEvent):
        """Логирование удаления события"""
        fields = [
            {"name": f"{Emojis.DOT} Название", "value": event.name, "inline": True},
            {"name": f"{Emojis.DOT} ID", "value": str(event.id), "inline": True},
            {"name": f"{Emojis.DOT} Создатель", "value": event.creator.mention if event.creator else "Неизвестно", "inline": True}
        ]
        
        await self.log_event(
            title=f"{Emojis.ERROR} Событие удалено",
            description=f"Удалено событие сервера",
            color='RED',
            fields=fields,
            thumbnail_url=event.cover.url if event.cover else None
        )
        
    async def log_event_location_update(self, before: ScheduledEvent, after: ScheduledEvent):
        """Логирование изменения локации события"""
        fields = [
            {"name": f"{Emojis.DOT} Событие", "value": after.name, "inline": True},
            {"name": f"{Emojis.DOT} Старая локация", "value": before.location or "Не указана", "inline": True},
            {"name": f"{Emojis.DOT} Новая локация", "value": after.location or "Не указана", "inline": True}
        ]
        
        await self.log_event(
            title=f"{Emojis.INFO} Изменена локация события",
            description=f"Обновлена локация события",
            color='BLUE',
            fields=fields,
            thumbnail_url=after.cover.url if after.cover else None
        )
        
    async def log_event_description_update(self, before: ScheduledEvent, after: ScheduledEvent):
        """Логирование изменения описания события"""
        fields = [
            {"name": f"{Emojis.DOT} Событие", "value": after.name, "inline": True},
            {"name": f"{Emojis.DOT} Старое описание", "value": before.description or "Не указано", "inline": False},
            {"name": f"{Emojis.DOT} Новое описание", "value": after.description or "Не указано", "inline": False}
        ]
        
        await self.log_event(
            title=f"{Emojis.INFO} Изменено описание события",
            description=f"Обновлено описание события",
            color='BLUE',
            fields=fields,
            thumbnail_url=after.cover.url if after.cover else None
        )
        
    async def log_event_name_update(self, before: ScheduledEvent, after: ScheduledEvent):
        """Логирование изменения названия события"""
        fields = [
            {"name": f"{Emojis.DOT} Старое название", "value": before.name, "inline": True},
            {"name": f"{Emojis.DOT} Новое название", "value": after.name, "inline": True}
        ]
        
        await self.log_event(
            title=f"{Emojis.INFO} Изменено название события",
            description=f"Событие было переименовано",
            color='BLUE',
            fields=fields,
            thumbnail_url=after.cover.url if after.cover else None
        )
        
    async def log_event_privacy_update(self, before: ScheduledEvent, after: ScheduledEvent):
        """Логирование изменения приватности события"""
        fields = [
            {"name": f"{Emojis.DOT} Событие", "value": after.name, "inline": True},
            {"name": f"{Emojis.DOT} Старый уровень", "value": str(before.privacy_level), "inline": True},
            {"name": f"{Emojis.DOT} Новый уровень", "value": str(after.privacy_level), "inline": True}
        ]
        
        await self.log_event(
            title=f"{Emojis.INFO} Изменена приватность события",
            description=f"Обновлен уровень приватности события",
            color='BLUE',
            fields=fields,
            thumbnail_url=after.cover.url if after.cover else None
        )
        
    async def log_event_start_time_update(self, before: ScheduledEvent, after: ScheduledEvent):
        """Логирование изменения времени начала события"""
        fields = [
            {"name": f"{Emojis.DOT} Событие", "value": after.name, "inline": True},
            {"name": f"{Emojis.DOT} Старое время", "value": discord.utils.format_dt(before.start_time), "inline": True},
            {"name": f"{Emojis.DOT} Новое время", "value": discord.utils.format_dt(after.start_time), "inline": True}
        ]
        
        await self.log_event(
            title=f"{Emojis.INFO} Изменено время начала события",
            description=f"Обновлено время начала события",
            color='BLUE',
            fields=fields,
            thumbnail_url=after.cover.url if after.cover else None
        )
        
    async def log_event_end_time_update(self, before: ScheduledEvent, after: ScheduledEvent):
        """Логирование изменения времени окончания события"""
        fields = [
            {"name": f"{Emojis.DOT} Событие", "value": after.name, "inline": True},
            {"name": f"{Emojis.DOT} Старое время", "value": discord.utils.format_dt(before.end_time) if before.end_time else "Не указано", "inline": True},
            {"name": f"{Emojis.DOT} Новое время", "value": discord.utils.format_dt(after.end_time) if after.end_time else "Не указано", "inline": True}
        ]
        
        await self.log_event(
            title=f"{Emojis.INFO} Изменено время окончания события",
            description=f"Обновлено время окончания события",
            color='BLUE',
            fields=fields,
            thumbnail_url=after.cover.url if after.cover else None
        )
        
    async def log_event_status_update(self, before: ScheduledEvent, after: ScheduledEvent):
        """Логирование изменения статуса события"""
        fields = [
            {"name": f"{Emojis.DOT} Событие", "value": after.name, "inline": True},
            {"name": f"{Emojis.DOT} Старый статус", "value": str(before.status), "inline": True},
            {"name": f"{Emojis.DOT} Новый статус", "value": str(after.status), "inline": True}
        ]
        
        await self.log_event(
            title=f"{Emojis.INFO} Изменен статус события",
            description=f"Обновлен статус события",
            color='BLUE',
            fields=fields,
            thumbnail_url=after.cover.url if after.cover else None
        )
        
    async def log_event_image_update(self, before: ScheduledEvent, after: ScheduledEvent):
        """Логирование изменения изображения события"""
        fields = [
            {"name": f"{Emojis.DOT} Событие", "value": after.name, "inline": True}
        ]
        
        await self.log_event(
            title=f"{Emojis.INFO} Изменено изображение события",
            description=f"Обновлено изображение события",
            color='BLUE',
            fields=fields,
            thumbnail_url=after.cover.url if after.cover else None
        )
        
    async def log_event_user_subscribe(self, event: ScheduledEvent, user: discord.User):
        """Логирование подписки пользователя на событие"""
        fields = [
            {"name": f"{Emojis.DOT} Событие", "value": event.name, "inline": True},
            {"name": f"{Emojis.DOT} Пользователь", "value": user.mention, "inline": True}
        ]
        
        await self.log_event(
            title=f"{Emojis.SUCCESS} Новый участник события",
            description=f"Пользователь подписался на событие",
            color='GREEN',
            fields=fields,
            thumbnail_url=event.cover.url if event.cover else None
        )
        
    async def log_event_user_unsubscribe(self, event: ScheduledEvent, user: discord.User):
        """Логирование отписки пользователя от события"""
        fields = [
            {"name": f"{Emojis.DOT} Событие", "value": event.name, "inline": True},
            {"name": f"{Emojis.DOT} Пользователь", "value": user.mention, "inline": True}
        ]
        
        await self.log_event(
            title=f"{Emojis.ERROR} Участник покинул событие",
            description=f"Пользователь отписался от события",
            color='RED',
            fields=fields,
            thumbnail_url=event.cover.url if event.cover else None
        ) 