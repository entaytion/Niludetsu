import discord
from ..tools.Emojis import Emojis
from Niludetsu.locale import _

from Niludetsu.webhooks.base import BaseLogger

class ReactionLogger(BaseLogger):

    async def log_reaction_add(self, log_channel: discord.TextChannel, payload: discord.RawReactionActionEvent, message: discord.Message, user: discord.User):
        t = _(guild_id=log_channel.guild.id, bot=self.bot)
        channel_info = f"<#{message.channel.id}> ({message.channel.id})"
        description = (
            f"**{t('audit_log', 'field_user')}:** {user.mention} ({user.id})\n"
            f"**{t('audit_log', 'field_reaction_emoji')}:** {payload.emoji}\n"
            f"**{t('audit_log', 'field_channel')}:** {channel_info}\n"
            f"**{t('audit_log', 'field_reaction_message')}:** [{t('audit_log', 'jump')}]({message.jump_url}) ({message.id})"
        )
        await self.webhooks.send_log(
            channel=log_channel,
            title=f"{Emojis.SUCCESS} {t('audit_log', 'reaction_add_title')}",
            description=description, fields=[],
            thumbnail_url=getattr(user, 'avatar', None) and user.avatar.url,
            guild=log_channel.guild,
        )

    async def log_reaction_remove(self, log_channel: discord.TextChannel, payload: discord.RawReactionActionEvent, message: discord.Message, user: discord.User):
        t = _(guild_id=log_channel.guild.id, bot=self.bot)
        channel_info = f"<#{message.channel.id}> ({message.channel.id})"
        description = (
            f"**{t('audit_log', 'field_user')}:** {user.mention} ({user.id})\n"
            f"**{t('audit_log', 'field_reaction_emoji')}:** {payload.emoji}\n"
            f"**{t('audit_log', 'field_channel')}:** {channel_info}\n"
            f"**{t('audit_log', 'field_reaction_message')}:** [{t('audit_log', 'jump')}]({message.jump_url}) ({message.id})"
        )
        await self.webhooks.send_log(
            channel=log_channel,
            title=f"{Emojis.ERROR} {t('audit_log', 'reaction_remove_title')}",
            description=description, fields=[],
            thumbnail_url=getattr(user, 'avatar', None) and user.avatar.url,
            guild=log_channel.guild,
        )

    async def log_reaction_clear(self, log_channel: discord.TextChannel, payload):
        t = _(guild_id=log_channel.guild.id, bot=self.bot)
        description = (
            f"**{t('audit_log', 'field_channel')}:** <#{payload.channel_id}>\n"
            f"**{t('audit_log', 'field_msg_id')}:** `{payload.message_id}`"
        )
        await self.webhooks.send_log(
            channel=log_channel,
            title=f"{Emojis.ERROR} {t('audit_log', 'reaction_clear_title')}",
            description=description,
            guild=log_channel.guild,
        )

    async def log_reaction_clear_emoji(self, log_channel: discord.TextChannel, payload):
        t = _(guild_id=log_channel.guild.id, bot=self.bot)
        description = (
            f"**{t('audit_log', 'field_channel')}:** <#{payload.channel_id}>\n"
            f"**{t('audit_log', 'field_msg_id')}:** `{payload.message_id}`\n"
            f"**{t('audit_log', 'field_reaction_emoji')}:** {payload.emoji}"
        )
        await self.webhooks.send_log(
            channel=log_channel,
            title=f"{Emojis.ERROR} {t('audit_log', 'reaction_clear_emoji_title')}",
            description=description,
            guild=log_channel.guild,
        )
