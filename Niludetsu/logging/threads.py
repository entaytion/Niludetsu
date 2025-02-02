from ..utils.logging import BaseLogger
from ..utils.constants import Emojis
import discord
from typing import Optional

class ThreadLogger(BaseLogger):
    """Логгер для тредов Discord."""
    
    async def log_thread_create(self, thread: discord.Thread):
        """Логирование создания треда"""
        fields = [
            {"name": f"{Emojis.DOT} Название", "value": thread.name, "inline": True},
            {"name": f"{Emojis.DOT} ID", "value": str(thread.id), "inline": True},
            {"name": f"{Emojis.DOT} Медленный режим", "value": f"{thread.slowmode_delay or 0} сек.", "inline": True},
            {"name": f"{Emojis.DOT} Длительность архивации", "value": f"{thread.auto_archive_duration} мин.", "inline": True},
            {"name": f"{Emojis.DOT} Создатель", "value": thread.owner.mention if thread.owner else "Неизвестно", "inline": True}
        ]
        
        if thread.parent:
            fields.append({"name": f"{Emojis.DOT} Родительский канал", "value": thread.parent.mention, "inline": True})
            description = f"В канале {thread.parent.mention} создан новый тред"
        else:
            fields.append({"name": f"{Emojis.DOT} Родительский канал", "value": "Канал недоступен", "inline": True})
            description = "Создан новый тред"
        
        await self.log_event(
            title=f"{Emojis.SUCCESS} Создан новый тред",
            description=description,
            color='GREEN',
            fields=fields
        )
        
    async def log_thread_delete(self, thread: discord.Thread):
        """Логирование удаления треда"""
        fields = [
            {"name": f"{Emojis.DOT} Название", "value": thread.name, "inline": True},
            {"name": f"{Emojis.DOT} ID", "value": str(thread.id), "inline": True},
            {"name": f"{Emojis.DOT} Родительский канал", "value": thread.parent.mention, "inline": True}
        ]
        
        await self.log_event(
            title=f"{Emojis.ERROR} Тред удален",
            description=f"Удален тред из канала {thread.parent.mention}",
            color='RED',
            fields=fields
        )
        
    async def log_thread_name_update(self, before: discord.Thread, after: discord.Thread):
        """Логирование изменения названия треда"""
        fields = [
            {"name": f"{Emojis.DOT} ID", "value": str(after.id), "inline": True},
            {"name": f"{Emojis.DOT} Старое название", "value": before.name, "inline": True},
            {"name": f"{Emojis.DOT} Новое название", "value": after.name, "inline": True}
        ]
        
        if after.parent:
            fields.append({"name": f"{Emojis.DOT} Родительский канал", "value": after.parent.mention, "inline": True})
            description = f"Обновлено название треда в канале {after.parent.mention}"
        else:
            fields.append({"name": f"{Emojis.DOT} Родительский канал", "value": "Канал недоступен", "inline": True})
            description = "Обновлено название треда"
        
        await self.log_event(
            title=f"{Emojis.INFO} Изменено название треда",
            description=description,
            color='BLUE',
            fields=fields
        )
        
    async def log_thread_slowmode_update(self, before: discord.Thread, after: discord.Thread):
        """Логирование изменения медленного режима треда"""
        fields = [
            {"name": f"{Emojis.DOT} Название", "value": after.name, "inline": True},
            {"name": f"{Emojis.DOT} Старая задержка", "value": f"{before.slowmode_delay or 0} сек.", "inline": True},
            {"name": f"{Emojis.DOT} Новая задержка", "value": f"{after.slowmode_delay or 0} сек.", "inline": True}
        ]
        
        if after.parent:
            fields.append({"name": f"{Emojis.DOT} Родительский канал", "value": after.parent.mention, "inline": True})
        else:
            fields.append({"name": f"{Emojis.DOT} Родительский канал", "value": "Канал недоступен", "inline": True})
        
        await self.log_event(
            title=f"{Emojis.INFO} Изменен медленный режим треда",
            description=f"Обновлена задержка сообщений в треде",
            color='BLUE',
            fields=fields
        )
        
    async def log_thread_archive_duration_update(self, before: discord.Thread, after: discord.Thread):
        """Логирование изменения длительности автоархивации треда"""
        fields = [
            {"name": f"{Emojis.DOT} Название", "value": after.name, "inline": True},
            {"name": f"{Emojis.DOT} Старая длительность", "value": f"{before.auto_archive_duration} мин.", "inline": True},
            {"name": f"{Emojis.DOT} Новая длительность", "value": f"{after.auto_archive_duration} мин.", "inline": True}
        ]
        
        if after.parent:
            fields.append({"name": f"{Emojis.DOT} Родительский канал", "value": after.parent.mention, "inline": True})
        else:
            fields.append({"name": f"{Emojis.DOT} Родительский канал", "value": "Канал недоступен", "inline": True})
        
        await self.log_event(
            title=f"{Emojis.INFO} Изменена длительность автоархивации",
            description=f"Обновлено время до автоматической архивации треда",
            color='BLUE',
            fields=fields
        )
        
    async def log_thread_archive(self, thread: discord.Thread):
        """Логирование архивации треда"""
        fields = [
            {"name": f"{Emojis.DOT} Название", "value": thread.name, "inline": True},
            {"name": f"{Emojis.DOT} ID", "value": str(thread.id), "inline": True}
        ]
        
        if thread.parent:
            fields.append({"name": f"{Emojis.DOT} Родительский канал", "value": thread.parent.mention, "inline": True})
        else:
            fields.append({"name": f"{Emojis.DOT} Родительский канал", "value": "Канал недоступен", "inline": True})
        
        await self.log_event(
            title=f"{Emojis.INFO} Тред архивирован",
            description=f"Тред был перемещен в архив",
            color='BLUE',
            fields=fields
        )
        
    async def log_thread_unarchive(self, thread: discord.Thread):
        """Логирование разархивации треда"""
        fields = [
            {"name": f"{Emojis.DOT} Название", "value": thread.name, "inline": True},
            {"name": f"{Emojis.DOT} ID", "value": str(thread.id), "inline": True}
        ]
        
        if thread.parent:
            fields.append({"name": f"{Emojis.DOT} Родительский канал", "value": thread.parent.mention, "inline": True})
        else:
            fields.append({"name": f"{Emojis.DOT} Родительский канал", "value": "Канал недоступен", "inline": True})
        
        await self.log_event(
            title=f"{Emojis.SUCCESS} Тред разархивирован",
            description=f"Тред был извлечен из архива",
            color='GREEN',
            fields=fields
        )
        
    async def log_thread_lock(self, thread: discord.Thread):
        """Логирование блокировки треда"""
        fields = [
            {"name": f"{Emojis.DOT} Название", "value": thread.name, "inline": True},
            {"name": f"{Emojis.DOT} ID", "value": str(thread.id), "inline": True}
        ]
        
        if thread.parent:
            fields.append({"name": f"{Emojis.DOT} Родительский канал", "value": thread.parent.mention, "inline": True})
        else:
            fields.append({"name": f"{Emojis.DOT} Родительский канал", "value": "Канал недоступен", "inline": True})
        
        await self.log_event(
            title=f"{Emojis.ERROR} Тред заблокирован",
            description=f"Тред был заблокирован для сообщений",
            color='RED',
            fields=fields
        )
        
    async def log_thread_unlock(self, thread: discord.Thread):
        """Логирование разблокировки треда"""
        fields = [
            {"name": f"{Emojis.DOT} Название", "value": thread.name, "inline": True},
            {"name": f"{Emojis.DOT} ID", "value": str(thread.id), "inline": True}
        ]
        
        if thread.parent:
            fields.append({"name": f"{Emojis.DOT} Родительский канал", "value": thread.parent.mention, "inline": True})
        else:
            fields.append({"name": f"{Emojis.DOT} Родительский канал", "value": "Канал недоступен", "inline": True})
        
        await self.log_event(
            title=f"{Emojis.SUCCESS} Тред разблокирован",
            description=f"Тред был разблокирован для сообщений",
            color='GREEN',
            fields=fields
        ) 