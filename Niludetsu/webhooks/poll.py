import discord
from Niludetsu import Emojis
from Niludetsu.webhooks.base import BaseLogger


class PollLogger(BaseLogger):
    """Логгер для опросов (Polls) — голоса за/против."""

    async def log_poll_vote_add(self, channel: discord.TextChannel, payload):
        """Пользователь проголосовал в опросе."""
        guild = self.bot.get_guild(payload.guild_id) if payload.guild_id else None
        user = guild.get_member(payload.user_id) if guild else None
        user_str = user.mention if user else f"<@{payload.user_id}>"

        # Получаем сообщение с опросом
        poll_info = ""
        try:
            poll_channel = guild.get_channel(payload.channel_id) if guild else None
            if poll_channel and hasattr(poll_channel, 'fetch_message'):
                msg = await poll_channel.fetch_message(payload.message_id)
                if msg and msg.poll:
                    poll_info = f"\n**Вопрос:** `{msg.poll.question.text}`"
                    # Найти за какой ответ проголосовал
                    if hasattr(payload, 'answer_id') and msg.poll.answers:
                        for answer in msg.poll.answers:
                            if answer.id == payload.answer_id:
                                poll_info += f"\n**Ответ:** `{answer.text}`"
                                break
        except Exception:
            pass

        description = (
            f"**Пользователь:** {user_str} (`{payload.user_id}`)\n"
            f"**Канал:** <#{payload.channel_id}>\n"
            f"**Сообщение:** `{payload.message_id}`"
            f"{poll_info}"
        )
        if hasattr(payload, 'answer_id'):
            description += f"\n**ID ответа:** `{payload.answer_id}`"

        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.SUCCESS} Опрос: голос добавлен",
            description=description, guild=guild,
            thumbnail_url=user.display_avatar.url if user else None,
        )

    async def log_poll_vote_remove(self, channel: discord.TextChannel, payload):
        """Пользователь убрал голос в опросе."""
        guild = self.bot.get_guild(payload.guild_id) if payload.guild_id else None
        user = guild.get_member(payload.user_id) if guild else None
        user_str = user.mention if user else f"<@{payload.user_id}>"

        poll_info = ""
        try:
            poll_channel = guild.get_channel(payload.channel_id) if guild else None
            if poll_channel and hasattr(poll_channel, 'fetch_message'):
                msg = await poll_channel.fetch_message(payload.message_id)
                if msg and msg.poll:
                    poll_info = f"\n**Вопрос:** `{msg.poll.question.text}`"
                    if hasattr(payload, 'answer_id') and msg.poll.answers:
                        for answer in msg.poll.answers:
                            if answer.id == payload.answer_id:
                                poll_info += f"\n**Ответ:** `{answer.text}`"
                                break
        except Exception:
            pass

        description = (
            f"**Пользователь:** {user_str} (`{payload.user_id}`)\n"
            f"**Канал:** <#{payload.channel_id}>\n"
            f"**Сообщение:** `{payload.message_id}`"
            f"{poll_info}"
        )
        if hasattr(payload, 'answer_id'):
            description += f"\n**ID ответа:** `{payload.answer_id}`"

        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.ERROR} Опрос: голос убран",
            description=description, guild=guild,
            thumbnail_url=user.display_avatar.url if user else None,
        )
