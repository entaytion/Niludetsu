import discord
from ..tools.Emojis import Emojis

from Niludetsu.webhooks.base import BaseLogger

class ReactionLogger(BaseLogger):
    """Логгер для событий реакций (добавление, удаление, очистка)."""

    async def log_reaction_add(self, log_channel: discord.TextChannel, payload: discord.RawReactionActionEvent, message: discord.Message, user: discord.User):
        channel_info = f"<#{message.channel.id}> ({message.channel.id})"
        description = (
            f"**Пользователь:** {user.mention} ({user.id})\n"
            f"**Эмодзи:** {payload.emoji}\n"
            f"**Канал:** {channel_info}\n"
            f"**Сообщение:** [перейти]({message.jump_url}) ({message.id})"
        )
        await self.webhooks.send_log(
            channel=log_channel,
            title=f"{Emojis.SUCCESS} Реакция: добавлена",
            description=description, fields=[],
            thumbnail_url=getattr(user, 'avatar', None) and user.avatar.url,
            guild=log_channel.guild,
        )

    async def log_reaction_remove(self, log_channel: discord.TextChannel, payload: discord.RawReactionActionEvent, message: discord.Message, user: discord.User):
        channel_info = f"<#{message.channel.id}> ({message.channel.id})"
        description = (
            f"**Пользователь:** {user.mention} ({user.id})\n"
            f"**Эмодзи:** {payload.emoji}\n"
            f"**Канал:** {channel_info}\n"
            f"**Сообщение:** [перейти]({message.jump_url}) ({message.id})"
        )
        await self.webhooks.send_log(
            channel=log_channel,
            title=f"{Emojis.ERROR} Реакция: удалена",
            description=description, fields=[],
            thumbnail_url=getattr(user, 'avatar', None) and user.avatar.url,
            guild=log_channel.guild,
        )

    async def log_reaction_clear(self, log_channel: discord.TextChannel, payload):
        """Sapphire: очистка всех реакций с сообщения."""
        description = (
            f"**Канал:** <#{payload.channel_id}>\n"
            f"**ID сообщения:** `{payload.message_id}`"
        )
        await self.webhooks.send_log(
            channel=log_channel,
            title=f"{Emojis.ERROR} Реакции: все очищены",
            description=description,
            guild=log_channel.guild,
        )

    async def log_reaction_clear_emoji(self, log_channel: discord.TextChannel, payload):
        """Sapphire: очистка реакций конкретного эмодзи."""
        description = (
            f"**Канал:** <#{payload.channel_id}>\n"
            f"**ID сообщения:** `{payload.message_id}`\n"
            f"**Эмодзи:** {payload.emoji}"
        )
        await self.webhooks.send_log(
            channel=log_channel,
            title=f"{Emojis.ERROR} Реакции: эмодзи очищен",
            description=description,
            guild=log_channel.guild,
        )
