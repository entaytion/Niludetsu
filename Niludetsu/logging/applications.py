from ..utils.logging import BaseLogger
from ..utils.constants import Emojis
import discord

class ApplicationLogger(BaseLogger):
    """Логгер для событий, связанных с приложениями Discord."""
    
    async def log_app_add(self, app: discord.Integration):
        """Логирование добавления приложения"""
        fields = [
            {"name": f"{Emojis.DOT} Название", "value": app.name, "inline": True},
            {"name": f"{Emojis.DOT} ID", "value": str(app.id), "inline": True},
            {"name": f"{Emojis.DOT} Тип", "value": app.type, "inline": True}
        ]
        
        await self.log_event(
            title=f"{Emojis.SUCCESS} Добавлено новое приложение",
            description="Приложение было добавлено на сервер",
            color='GREEN',
            fields=fields,
            thumbnail_url=app.icon_url if hasattr(app, 'icon_url') else None
        )
        
    async def log_app_remove(self, app: discord.Integration):
        """Логирование удаления приложения"""
        fields = [
            {"name": f"{Emojis.DOT} Название", "value": app.name, "inline": True},
            {"name": f"{Emojis.DOT} ID", "value": str(app.id), "inline": True},
            {"name": f"{Emojis.DOT} Тип", "value": app.type, "inline": True}
        ]
        
        await self.log_event(
            title=f"{Emojis.ERROR} Приложение удалено",
            description="Приложение было удалено с сервера",
            color='RED',
            fields=fields,
            thumbnail_url=app.icon_url if hasattr(app, 'icon_url') else None
        )
        
    async def log_app_permission_update(self, app_command):
        """Логирование обновления разрешений команды приложения"""
        fields = [
            {"name": f"{Emojis.DOT} Команда", "value": app_command.name, "inline": True},
            {"name": f"{Emojis.DOT} ID", "value": str(app_command.id), "inline": True},
            {"name": f"{Emojis.DOT} Тип", "value": app_command.type, "inline": True}
        ]
        
        await self.log_event(
            title=f"{Emojis.INFO} Обновление разрешений команды",
            description="Разрешения команды приложения были обновлены",
            color='BLUE',
            fields=fields
        ) 