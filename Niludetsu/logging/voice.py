from ..utils.logging import BaseLogger, LoggingState
from ..utils.constants import Emojis
from ..utils.embed import Embed
import discord
from typing import Optional
import traceback

class VoiceLogger(BaseLogger):
    """Логгер для голосовых каналов Discord."""
    
    def __init__(self, bot: discord.Client):
        super().__init__(bot)
        self.log_channel = None
        bot.loop.create_task(self._initialize())
    
    async def _initialize(self):
        """Инициализация логгера"""
        await self.bot.wait_until_ready()
        await self.initialize_logs()
        self.log_channel = LoggingState.log_channel
    
    async def log_voice_channel_full(self, channel: discord.VoiceChannel):
        """Логирование заполнения голосового канала"""
        fields = [
            {"name": f"{Emojis.DOT} Канал", "value": channel.mention, "inline": True},
            {"name": f"{Emojis.DOT} ID", "value": str(channel.id), "inline": True},
            {"name": f"{Emojis.DOT} Лимит", "value": str(channel.user_limit), "inline": True},
            {"name": f"{Emojis.DOT} Категория", "value": channel.category.name if channel.category else "Нет", "inline": True}
        ]
        
        await self.log_event(
            title=f"{Emojis.INFO} Голосовой канал заполнен",
            description=f"Голосовой канал достиг максимального количества участников",
            color='BLUE',
            fields=fields
        )
        
    async def log_voice_user_join(self, member: discord.Member, channel: discord.VoiceChannel):
        """Логирование присоединения пользователя к голосовому каналу"""
        fields = [
            {"name": f"{Emojis.DOT} Пользователь", "value": member.mention, "inline": True},
            {"name": f"{Emojis.DOT} ID пользователя", "value": str(member.id), "inline": True},
            {"name": f"{Emojis.DOT} Канал", "value": channel.mention, "inline": True},
            {"name": f"{Emojis.DOT} Участников", "value": f"{len(channel.members)}/{channel.user_limit if channel.user_limit else '∞'}", "inline": True}
        ]
        
        await self.log_event(
            title=f"{Emojis.SUCCESS} Пользователь присоединился к голосовому каналу",
            description=f"Пользователь подключился к голосовому каналу",
            color='GREEN',
            fields=fields,
            thumbnail_url=member.display_avatar.url
        )
        
    async def log_voice_user_switch(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None:
        """Логирование перехода пользователя между каналами"""
        fields = [
            {"name": f"{Emojis.DOT} Предыдущий канал", "value": before.channel.mention if before.channel else "Нет", "inline": True},
            {"name": f"{Emojis.DOT} Новый канал", "value": after.channel.mention if after.channel else "Нет", "inline": True}
        ]
        
        await self.log_event(
            title=f"{Emojis.INFO} Изменение голосового канала",
            description=f"{member.mention} сменил канал",
            color='BLUE',
            fields=fields,
            thumbnail_url=member.display_avatar.url
        )
        
    async def log_voice_user_leave(self, member: discord.Member, channel: discord.VoiceChannel):
        """Логирование выхода пользователя из голосового канала"""
        fields = [
            {"name": f"{Emojis.DOT} Пользователь", "value": member.mention, "inline": True},
            {"name": f"{Emojis.DOT} ID пользователя", "value": str(member.id), "inline": True},
            {"name": f"{Emojis.DOT} Канал", "value": channel.mention, "inline": True},
            {"name": f"{Emojis.DOT} Участников", "value": f"{len(channel.members)}/{channel.user_limit if channel.user_limit else '∞'}", "inline": True}
        ]
        
        await self.log_event(
            title=f"{Emojis.ERROR} Пользователь покинул голосовой канал",
            description=f"Пользователь отключился от голосового канала",
            color='RED',
            fields=fields,
            thumbnail_url=member.display_avatar.url
        )
        
    async def log_voice_user_move(self, member: discord.Member, executor: discord.Member, before: discord.VoiceChannel, after: discord.VoiceChannel):
        """Логирование принудительного перемещения пользователя между голосовыми каналами"""
        fields = [
            {"name": f"{Emojis.DOT} Пользователь", "value": member.mention, "inline": True},
            {"name": f"{Emojis.DOT} ID пользователя", "value": str(member.id), "inline": True},
            {"name": f"{Emojis.DOT} Модератор", "value": executor.mention, "inline": True},
            {"name": f"{Emojis.DOT} Предыдущий канал", "value": before.mention, "inline": True},
            {"name": f"{Emojis.DOT} Новый канал", "value": after.mention, "inline": True}
        ]
        
        await self.log_event(
            title=f"{Emojis.INFO} Пользователь перемещен в другой канал",
            description=f"Пользователь был принудительно перемещен в другой голосовой канал",
            color='BLUE',
            fields=fields,
            thumbnail_url=member.display_avatar.url
        )
        
    async def log_voice_user_kick(self, member: discord.Member, executor: discord.Member, channel: discord.VoiceChannel):
        """Логирование принудительного отключения пользователя от голосового канала"""
        fields = [
            {"name": f"{Emojis.DOT} Пользователь", "value": member.mention, "inline": True},
            {"name": f"{Emojis.DOT} ID пользователя", "value": str(member.id), "inline": True},
            {"name": f"{Emojis.DOT} Модератор", "value": executor.mention, "inline": True},
            {"name": f"{Emojis.DOT} Канал", "value": channel.mention, "inline": True}
        ]
        
        await self.log_event(
            title=f"{Emojis.ERROR} Пользователь отключен от голосового канала",
            description=f"Пользователь был принудительно отключен от голосового канала",
            color='RED',
            fields=fields,
            thumbnail_url=member.display_avatar.url
        )

    async def log_voice_status_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Логирование изменений статуса голосового канала"""
        try:
            if not before.channel and after.channel:  # Пользователь присоединился
                await self.log_voice_user_join(member, after.channel)
            elif before.channel and not after.channel:  # Пользователь отключился
                await self.log_voice_user_leave(member, before.channel)
            elif before.channel and after.channel and before.channel != after.channel:  # Пользователь перешел в другой канал
                await self.log_voice_user_switch(member, before, after)
        except Exception as e:
            print(f"❌ Ошибка при логировании голосового события: {e}")
            traceback.print_exc() 