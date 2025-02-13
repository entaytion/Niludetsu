from Niludetsu import BaseLogger, Emojis, LoggingState
import discord
from typing import Optional

class InviteLogger(BaseLogger):
    """Логгер для приглашений Discord."""
    
    def __init__(self, bot: discord.Client):
        super().__init__(bot)
        self.log_channel = None
        bot.loop.create_task(self._initialize())
    
    async def _initialize(self):
        """Инициализация логгера"""
        await self.bot.wait_until_ready()
        await self.initialize_logs()
        self.log_channel = LoggingState.log_channel
        
    async def log_invite_create(self, invite: discord.Invite):
        """Логирование создания приглашения"""
        fields = [
            {"name": f"{Emojis.DOT} Создатель", "value": invite.inviter.mention if invite.inviter else "Система", "inline": True},
            {"name": f"{Emojis.DOT} Код", "value": invite.code, "inline": True},
            {"name": f"{Emojis.DOT} Канал", "value": invite.channel.mention if invite.channel else "Неизвестно", "inline": True},
            {"name": f"{Emojis.DOT} Макс. использований", "value": str(invite.max_uses) if invite.max_uses else "∞", "inline": True},
            {"name": f"{Emojis.DOT} Срок действия", "value": discord.utils.format_dt(invite.expires_at) if invite.expires_at else "∞", "inline": True},
            {"name": f"{Emojis.DOT} Временное", "value": "Да" if invite.temporary else "Нет", "inline": True}
        ]
        
        await self.log_event(
            title=f"{Emojis.SUCCESS} Создано новое приглашение",
            description=f"Создана новая ссылка-приглашение discord.gg/{invite.code}",
            color='GREEN',
            fields=fields
        )
        
    async def log_invite_delete(self, invite: discord.Invite):
        """Логирование удаления приглашения"""
        fields = [
            {"name": f"{Emojis.DOT} Создатель", "value": invite.inviter.mention if invite.inviter else "Система", "inline": True},
            {"name": f"{Emojis.DOT} Код", "value": invite.code, "inline": True},
            {"name": f"{Emojis.DOT} Канал", "value": invite.channel.mention if invite.channel else "Неизвестно", "inline": True},
            {"name": f"{Emojis.DOT} Использований", "value": str(invite.uses) if invite.uses else "0", "inline": True}
        ]
        
        await self.log_event(
            title=f"{Emojis.ERROR} Приглашение удалено",
            description=f"Удалена ссылка-приглашение discord.gg/{invite.code}",
            color='RED',
            fields=fields
        )
        
    async def log_invite_post(self, invite: discord.Invite, message: discord.Message):
        """Логирование публикации приглашения в чат"""
        fields = [
            {"name": f"{Emojis.DOT} Автор", "value": message.author.mention, "inline": True},
            {"name": f"{Emojis.DOT} Канал", "value": message.channel.mention, "inline": True},
            {"name": f"{Emojis.DOT} Приглашение", "value": f"discord.gg/{invite.code}", "inline": True},
            {"name": f"{Emojis.DOT} Целевой сервер", "value": invite.guild.name if invite.guild else "Неизвестно", "inline": True},
            {"name": f"{Emojis.DOT} Создатель приглашения", "value": invite.inviter.mention if invite.inviter else "Система", "inline": True}
        ]
        
        await self.log_event(
            title=f"{Emojis.WARNING} Опубликовано приглашение",
            description=f"В чат отправлена ссылка-приглашение на сервер",
            color='YELLOW',
            fields=fields
        ) 