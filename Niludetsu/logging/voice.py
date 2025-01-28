from ..core.base import BaseLogger, EMOJIS
import discord
from typing import Optional

class VoiceLogger(BaseLogger):
    """Логгер для голосовых каналов Discord."""
    
    async def log_voice_channel_full(self, channel: discord.VoiceChannel):
        """Логирование заполнения голосового канала"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Канал", "value": channel.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} ID", "value": str(channel.id), "inline": True},
            {"name": f"{EMOJIS['DOT']} Лимит", "value": str(channel.user_limit), "inline": True},
            {"name": f"{EMOJIS['DOT']} Категория", "value": channel.category.name if channel.category else "Нет", "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['INFO']} Голосовой канал заполнен",
            description=f"Голосовой канал достиг максимального количества участников",
            color='BLUE',
            fields=fields
        )
        
    async def log_voice_user_join(self, member: discord.Member, channel: discord.VoiceChannel):
        """Логирование присоединения пользователя к голосовому каналу"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Пользователь", "value": member.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} ID пользователя", "value": str(member.id), "inline": True},
            {"name": f"{EMOJIS['DOT']} Канал", "value": channel.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} Участников", "value": f"{len(channel.members)}/{channel.user_limit if channel.user_limit else '∞'}", "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['SUCCESS']} Пользователь присоединился к голосовому каналу",
            description=f"Пользователь подключился к голосовому каналу",
            color='GREEN',
            fields=fields,
            thumbnail_url=member.display_avatar.url
        )
        
    async def log_voice_user_switch(self, member: discord.Member, before: discord.VoiceChannel, after: discord.VoiceChannel):
        """Логирование перехода пользователя между голосовыми каналами"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Пользователь", "value": member.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} ID пользователя", "value": str(member.id), "inline": True},
            {"name": f"{EMOJIS['DOT']} Предыдущий канал", "value": before.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} Новый канал", "value": after.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} Участников (предыдущий)", "value": f"{len(before.members)}/{before.user_limit if before.user_limit else '∞'}", "inline": True},
            {"name": f"{EMOJIS['DOT']} Участников (новый)", "value": f"{len(after.members)}/{after.user_limit if after.user_limit else '∞'}", "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['INFO']} Пользователь сменил голосовой канал",
            description=f"Пользователь перешел в другой голосовой канал",
            color='BLUE',
            fields=fields,
            thumbnail_url=member.display_avatar.url
        )
        
    async def log_voice_user_leave(self, member: discord.Member, channel: discord.VoiceChannel):
        """Логирование выхода пользователя из голосового канала"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Пользователь", "value": member.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} ID пользователя", "value": str(member.id), "inline": True},
            {"name": f"{EMOJIS['DOT']} Канал", "value": channel.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} Участников", "value": f"{len(channel.members)}/{channel.user_limit if channel.user_limit else '∞'}", "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['ERROR']} Пользователь покинул голосовой канал",
            description=f"Пользователь отключился от голосового канала",
            color='RED',
            fields=fields,
            thumbnail_url=member.display_avatar.url
        )
        
    async def log_voice_user_move(self, member: discord.Member, executor: discord.Member, before: discord.VoiceChannel, after: discord.VoiceChannel):
        """Логирование принудительного перемещения пользователя между голосовыми каналами"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Пользователь", "value": member.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} ID пользователя", "value": str(member.id), "inline": True},
            {"name": f"{EMOJIS['DOT']} Модератор", "value": executor.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} Предыдущий канал", "value": before.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} Новый канал", "value": after.mention, "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['INFO']} Пользователь перемещен в другой канал",
            description=f"Пользователь был принудительно перемещен в другой голосовой канал",
            color='BLUE',
            fields=fields,
            thumbnail_url=member.display_avatar.url
        )
        
    async def log_voice_user_kick(self, member: discord.Member, executor: discord.Member, channel: discord.VoiceChannel):
        """Логирование принудительного отключения пользователя от голосового канала"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Пользователь", "value": member.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} ID пользователя", "value": str(member.id), "inline": True},
            {"name": f"{EMOJIS['DOT']} Модератор", "value": executor.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} Канал", "value": channel.mention, "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['ERROR']} Пользователь отключен от голосового канала",
            description=f"Пользователь был принудительно отключен от голосового канала",
            color='RED',
            fields=fields,
            thumbnail_url=member.display_avatar.url
        )

    async def log_voice_status_update(self, member: discord.Member, before: Optional[discord.VoiceChannel], after: Optional[discord.VoiceChannel]):
        """Логирование изменений статуса голосового канала"""
        if not before and after:  # Пользователь присоединился
            await self.log_voice_user_join(member, after)
        elif before and not after:  # Пользователь отключился
            await self.log_voice_user_leave(member, before)
        elif before and after and before != after:  # Пользователь перешел в другой канал
            await self.log_voice_user_switch(member, before, after) 