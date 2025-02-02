from ..utils.logging import BaseLogger
from ..utils.constants import Emojis
import discord
from discord.ext import commands
from typing import Optional, Union
import traceback

class ErrorLogger(BaseLogger):
    """Логгер для обработки и логирования ошибок."""
    
    async def log_command_error(self, ctx: Union[commands.Context, discord.Interaction], error: Exception):
        """Логирование ошибок команд с автоматическим определением типа контекста"""
        if isinstance(ctx, discord.Interaction):
            command_name = f"/{ctx.command.parent.name if ctx.command.parent else ''}{' ' if ctx.command.parent else ''}{ctx.command.name}"
            author = ctx.user
            channel = ctx.channel
        else:
            command_name = ctx.message.content
            author = ctx.author
            channel = ctx.channel
            
        error_trace = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
        
        # Уведомление владельца бота
        if self.owner_id:
            await self.log_channel.send(f"<@{self.owner_id}>, произошла ошибка!")
            
        fields = [
            {"name": f"{Emojis.DOT} Команда", "value": f"`{command_name}`", "inline": True},
            {"name": f"{Emojis.DOT} Автор", "value": f"{author.mention} (`{author.id}`)", "inline": True},
            {"name": f"{Emojis.DOT} Канал", "value": channel.mention, "inline": True},
            {"name": f"{Emojis.DOT} Ошибка", "value": f"```py\n{error_trace[:1900]}```", "inline": False}
        ]
        
        await self.log_event(
            title=f"{Emojis.ERROR} Ошибка команды",
            description="",
            color='RED',
            fields=fields,
            author={'name': 'Command Error'}
        )
        
    async def log_general_error(self, error: Exception, context: str = None):
        """Логирование общих ошибок, не связанных с командами"""
        error_trace = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
        
        fields = [
            {"name": f"{Emojis.DOT} Контекст", "value": context or "Общая ошибка", "inline": False},
            {"name": f"{Emojis.DOT} Ошибка", "value": f"```py\n{error_trace[:1900]}```", "inline": False}
        ]
        
        await self.log_event(
            title=f"{Emojis.WARNING} Общая ошибка",
            description="",
            color='RED',
            fields=fields,
            author={'name': 'System Error'}
        )
        
    async def log_api_error(self, error: Exception, endpoint: str, method: str = "GET"):
        """Логирование ошибок API запросов"""
        error_trace = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
        
        fields = [
            {"name": f"{Emojis.DOT} Метод", "value": method, "inline": True},
            {"name": f"{Emojis.DOT} Эндпоинт", "value": endpoint, "inline": True},
            {"name": f"{Emojis.DOT} Ошибка", "value": f"```py\n{error_trace[:1900]}```", "inline": False}
        ]
        
        await self.log_event(
            title=f"{Emojis.ERROR} Ошибка API",
            description="",
            color='RED',
            fields=fields,
            author={'name': 'API Error'}
        ) 