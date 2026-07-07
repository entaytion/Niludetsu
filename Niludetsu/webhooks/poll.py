import discord
from ..tools.Emojis import Emojis
from Niludetsu.locale import _

from Niludetsu.webhooks.base import BaseLogger

class PollLogger(BaseLogger):
    """Логгер для опросов (Polls) — голоса за/против."""

    async def log_poll_vote_add(self, channel: discord.TextChannel, payload):
        """Пользователь проголосовал в опросе."""
        guild = self.bot.get_guild(payload.guild_id) if payload.guild_id else None
        user = guild.get_member(payload.user_id) if guild else None
        user_str = user.mention if user else f"<@{payload.user_id}>"

        t = _(guild_id=payload.guild_id, bot=self.bot)

        poll_info = ""
        try:
            poll_channel = guild.get_channel(payload.channel_id) if guild else None
            if poll_channel and hasattr(poll_channel, 'fetch_message'):
                msg = await poll_channel.fetch_message(payload.message_id)
                if msg and msg.poll:
                    poll_info = f"\n**{t('audit_log', 'field_poll_question')}:** `{msg.poll.question.text}`"
                    if hasattr(payload, 'answer_id') and msg.poll.answers:
                        for answer in msg.poll.answers:
                            if answer.id == payload.answer_id:
                                poll_info += f"\n**{t('audit_log', 'field_poll_answer')}:** `{answer.text}`"
                                break
        except Exception:
            pass

        description = (
            f"**{t('audit_log', 'field_user')}:** {user_str} (`{payload.user_id}`)\n"
            f"**{t('audit_log', 'field_channel')}:** <#{payload.channel_id}>\n"
            f"**{t('audit_log', 'field_reaction_message')}:** `{payload.message_id}`"
            f"{poll_info}"
        )
        if hasattr(payload, 'answer_id'):
            description += f"\n**{t('audit_log', 'field_poll_answer_id')}:** `{payload.answer_id}`"

        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.SUCCESS} {t('audit_log', 'poll_vote_add_title')}",
            description=description, guild=guild,
            thumbnail_url=user.display_avatar.url if user else None,
        )

    async def log_poll_vote_remove(self, channel: discord.TextChannel, payload):
        """Пользователь убрал голос в опросе."""
        guild = self.bot.get_guild(payload.guild_id) if payload.guild_id else None
        user = guild.get_member(payload.user_id) if guild else None
        user_str = user.mention if user else f"<@{payload.user_id}>"

        t = _(guild_id=payload.guild_id, bot=self.bot)

        poll_info = ""
        try:
            poll_channel = guild.get_channel(payload.channel_id) if guild else None
            if poll_channel and hasattr(poll_channel, 'fetch_message'):
                msg = await poll_channel.fetch_message(payload.message_id)
                if msg and msg.poll:
                    poll_info = f"\n**{t('audit_log', 'field_poll_question')}:** `{msg.poll.question.text}`"
                    if hasattr(payload, 'answer_id') and msg.poll.answers:
                        for answer in msg.poll.answers:
                            if answer.id == payload.answer_id:
                                poll_info += f"\n**{t('audit_log', 'field_poll_answer')}:** `{answer.text}`"
                                break
        except Exception:
            pass

        description = (
            f"**{t('audit_log', 'field_user')}:** {user_str} (`{payload.user_id}`)\n"
            f"**{t('audit_log', 'field_channel')}:** <#{payload.channel_id}>\n"
            f"**{t('audit_log', 'field_reaction_message')}:** `{payload.message_id}`"
            f"{poll_info}"
        )
        if hasattr(payload, 'answer_id'):
            description += f"\n**{t('audit_log', 'field_poll_answer_id')}:** `{payload.answer_id}`"

        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.ERROR} {t('audit_log', 'poll_vote_remove_title')}",
            description=description, guild=guild,
            thumbnail_url=user.display_avatar.url if user else None,
        )
