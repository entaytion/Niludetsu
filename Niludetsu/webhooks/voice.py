import discord
from ..tools.Emojis import Emojis

from Niludetsu.webhooks.base import BaseLogger

class VoiceLogger(BaseLogger):
    """Логгер для действий в голосовых каналах."""

    async def log_voice_join(self, log_channel: discord.TextChannel, member: discord.Member, channel: discord.VoiceChannel):
        description = (
            f"**Пользователь:** {member.mention} (`{member.id}`)\n"
            f"**Канал:** {channel.mention} (`{channel.id}`)\n"
            f"**Категория:** `{channel.category.name if channel.category else 'Нет'}`\n"
            f"**Участников в канале:** `{len(channel.members)}/{channel.user_limit if channel.user_limit else '∞'}`"
        )
        await self.webhooks.send_log(
            channel=log_channel,
            title=f"{Emojis.SUCCESS} Голосовой канал: пользователь присоединился",
            description=description,
            thumbnail_url=member.display_avatar.url,
            guild=member.guild,
        )

    async def log_voice_leave(self, log_channel: discord.TextChannel, member: discord.Member, channel: discord.VoiceChannel):
        description = (
            f"**Пользователь:** {member.mention} (`{member.id}`)\n"
            f"**Канал:** {channel.mention} (`{channel.id}`)\n"
            f"**Категория:** `{channel.category.name if channel.category else 'Нет'}`\n"
            f"**Участников в канале:** `{len(channel.members)}/{channel.user_limit if channel.user_limit else '∞'}`"
        )
        await self.webhooks.send_log(
            channel=log_channel,
            title=f"{Emojis.ERROR} Голосовой канал: пользователь покинул",
            description=description,
            thumbnail_url=member.display_avatar.url,
            guild=member.guild,
        )

    async def log_voice_switch(self, log_channel: discord.TextChannel, member: discord.Member, before: discord.VoiceChannel, after: discord.VoiceChannel):
        description = (
            f"**Пользователь:** {member.mention} (`{member.id}`)\n"
            f"**Канал:** {before.mention if before else '`Нет`'} ➜ {after.mention if after else '`Нет`'}\n"
            f"**Категория:** `{before.category.name if before and before.category else 'Нет'}` ➜ `{after.category.name if after and after.category else 'Нет'}`"
        )
        fields = []
        if before and after:
            fields.append({
                "name": "> Изменения:",
                "value": (
                    f"**Участников в старом канале:** `{len(before.members)}/{before.user_limit if before.user_limit else '∞'}`\n"
                    f"**Участников в новом канале:** `{len(after.members)}/{after.user_limit if after.user_limit else '∞'}`"
                ),
                "inline": False,
            })
        await self.webhooks.send_log(
            channel=log_channel,
            title=f"{Emojis.UNKNOWN} Голосовой канал: пользователь перешел",
            description=description, fields=fields,
            thumbnail_url=member.display_avatar.url,
            guild=member.guild,
        )

    async def log_voice_move(self, log_channel: discord.TextChannel, member: discord.Member, before: discord.VoiceChannel, after: discord.VoiceChannel, moderator: discord.User = None):
        """Sapphire: Voice User Move — перемещение модератором."""
        description = (
            f"**Пользователь:** {member.mention} (`{member.id}`)\n"
            f"**Канал:** {before.mention} ➜ {after.mention}"
        )
        if moderator:
            description += f"\n**Модератор:** {moderator.mention} (`{moderator.id}`)"
        await self.webhooks.send_log(
            channel=log_channel,
            title=f"{Emojis.UNKNOWN} Голосовой канал: пользователь перемещён",
            description=description,
            thumbnail_url=member.display_avatar.url,
            guild=member.guild,
        )

    async def log_voice_disconnect(self, log_channel: discord.TextChannel, member: discord.Member, channel: discord.VoiceChannel, moderator: discord.User = None):
        """Sapphire: Voice User Kick — отключение модератором."""
        description = (
            f"**Пользователь:** {member.mention} (`{member.id}`)\n"
            f"**Канал:** {channel.mention} (`{channel.id}`)"
        )
        if moderator:
            description += f"\n**Модератор:** {moderator.mention} (`{moderator.id}`)"
        await self.webhooks.send_log(
            channel=log_channel,
            title=f"{Emojis.ERROR} Голосовой канал: пользователь отключён",
            description=description,
            thumbnail_url=member.display_avatar.url,
            guild=member.guild,
        )

    async def log_voice_state(self, log_channel: discord.TextChannel, member: discord.Member, changes: dict):
        STATE_LABELS = {
            'deaf': 'Серверный звук',
            'mute': 'Серверный микрофон',
            'self_deaf': 'Звук (самостоятельно)',
            'self_mute': 'Микрофон (самостоятельно)',
            'self_stream': 'Стрим',
            'self_video': 'Видео',
        }
        description = f"**Пользователь:** {member.mention} (`{member.id}`)"
        fields = []
        for change_type, (before, after) in changes.items():
            label = STATE_LABELS.get(change_type, change_type)
            fields.append({
                "name": "> Изменения:",
                "value": f"**{label}:** `{'Вкл' if before else 'Выкл'}` ➜ `{'Вкл' if after else 'Выкл'}`",
                "inline": False,
            })
        if not fields:
            return
        await self.webhooks.send_log(
            channel=log_channel,
            title=f"{Emojis.UNKNOWN} Голосовой канал: состояние обновлено",
            description=description, fields=fields,
            thumbnail_url=member.display_avatar.url,
            guild=member.guild,
        )
