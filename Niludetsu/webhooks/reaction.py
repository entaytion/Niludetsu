import discord
from Niludetsu import Emojis
from Niludetsu.development.Webhooks import Webhooks

class ReactionLogger:
    """
    Логгер для событий реакций через вебхук (кто поставил/снял, где, на что, какой эмодзи).
    """
    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.webhooks = Webhooks(bot)

    async def log_reaction_add(self, log_channel: discord.TextChannel, payload: discord.RawReactionActionEvent, message: discord.Message, user: discord.User):
        # Определяем канал, где была реакция
        channel_info = f"<#{message.channel.id}> ({message.channel.id})" if hasattr(message.channel, 'mention') else f"ID: {message.channel.id}"
        title = f"{Emojis.SUCCESS} Реакция: добавлена"
        description = (
            f"**Пользователь:** {user.mention} ({user.id})\n"
            f"**Эмодзи:** {payload.emoji}\n"
            f"**Канал:** {channel_info}\n"
            f"**Сообщение:** [перейти]({message.jump_url}) ({message.id})"
        )
        await self.webhooks.send_log(
            channel=log_channel,
            title=title,
            description=description,
            fields=[],
            thumbnail_url=getattr(user, 'avatar', None) and user.avatar.url,
            guild=log_channel.guild
        )

    async def log_reaction_remove(self, log_channel: discord.TextChannel, payload: discord.RawReactionActionEvent, message: discord.Message, user: discord.User):
        channel_info = f"<#{message.channel.id}> ({message.channel.id})" if hasattr(message.channel, 'mention') else f"ID: {message.channel.id}"
        title = f"{Emojis.ERROR} Реакция: удалена"
        description = (
            f"**Пользователь:** {user.mention} ({user.id})\n"
            f"**Эмодзи:** {payload.emoji}\n"
            f"**Канал:** {channel_info}\n"
            f"**Сообщение:** [перейти]({message.jump_url}) ({message.id})"
        )
        await self.webhooks.send_log(
            channel=log_channel,
            title=title,
            description=description,
            fields=[],
            thumbnail_url=getattr(user, 'avatar', None) and user.avatar.url,
            guild=log_channel.guild
        )

