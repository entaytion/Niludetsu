from ..core.base import BaseLogger, LoggingState
import discord
from discord.ext import commands
from typing import Optional, Union

class Logger(BaseLogger):
    """Основной класс логгера."""
    
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
        self.logging_enabled: bool = True

    async def setup(self, webhook_url: str, log_channel_id: int) -> None:
        """Настройка логгера."""
        if not LoggingState.initialized:
            await self.initialize_logs()
        
    async def log_error(self, 
                       error: Exception, 
                       command_name: str = None, 
                       user: Union[discord.Member, discord.User] = None) -> None:
        """Логирование ошибок."""
        if not self.logging_enabled or not LoggingState.initialized:
            return
            
        title = "🚫 Ошибка"
        description = f"```py\n{str(error)}\n```"
        
        fields = []
        if command_name:
            fields.append({"name": "Команда", "value": command_name, "inline": True})
        if user:
            fields.append({
                "name": "Пользователь",
                "value": f"{user.name} ({user.id})",
                "inline": True
            })
            
        await self.log_event(
            title=title,
            description=description,
            color='RED',
            fields=fields,
            footer={"text": "Система логирования"}
        )
        
    async def log_command(self, 
                         ctx: commands.Context, 
                         command_name: str,
                         status: str = "✅ Успешно") -> None:
        """Логирование использования команд."""
        if not self.logging_enabled or not LoggingState.initialized:
            return
            
        await self.log_event(
            title=f"Использование команды: {command_name}",
            description=f"Статус: {status}",
            fields=[
                {"name": "Пользователь", "value": f"{ctx.author} ({ctx.author.id})", "inline": True},
                {"name": "Канал", "value": f"{ctx.channel.name} ({ctx.channel.id})", "inline": True}
            ],
            color='GREEN' if status.startswith("✅") else 'RED'
        )

    async def log_event(self, *args, **kwargs):
        """Обертка для проверки статуса логирования"""
        if self.logging_enabled and LoggingState.initialized:
            await super().log_event(*args, **kwargs) 