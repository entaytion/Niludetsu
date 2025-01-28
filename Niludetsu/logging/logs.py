from ..core.base import BaseLogger
import discord
from discord.ext import commands
from typing import Optional, Union

class Logger(BaseLogger):
    """Основной класс логгера."""
    
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
        self.log_channel_id: Optional[int] = None
        self.logging_enabled: bool = True

    async def setup(self, webhook_url: str, log_channel_id: int) -> None:
        """Настройка логгера."""
        await self.initialize_webhook(webhook_url)
        self.log_channel_id = log_channel_id
        
    async def log_error(self, 
                       error: Exception, 
                       command_name: str = None, 
                       user: Union[discord.Member, discord.User] = None) -> None:
        """Логирование ошибок."""
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
            
        await self.send_log(
            title=title,
            description=description,
            color=0xFF0000,
            fields=fields,
            footer={"text": "Система логирования"}
        )
        
    async def log_command(self, 
                         ctx: commands.Context, 
                         command_name: str,
                         status: str = "✅ Успешно") -> None:
        """Логирование использования команд."""
        await self.send_log(
            title=f"Использование команды: {command_name}",
            description=f"Статус: {status}",
            fields=[
                {"name": "Пользователь", "value": f"{ctx.author} ({ctx.author.id})", "inline": True},
                {"name": "Канал", "value": f"{ctx.channel.name} ({ctx.channel.id})", "inline": True}
            ],
            color=0x2ECC71 if status.startswith("✅") else 0xE74C3C
        )

    async def log_event(self, *args, **kwargs):
        """Обертка для проверки статуса логирования"""
        if self.logging_enabled:
            await super().log_event(*args, **kwargs) 