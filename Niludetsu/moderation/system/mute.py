import discord
from datetime import datetime
from Niludetsu.moderation.config import ActionType
from Niludetsu.moderation.exceptions import ModerationError
from Niludetsu.moderation.manager import ModerationManager
from Niludetsu.tools.Time import TimeService
from typing import Optional

_time = TimeService()

class MuteSystem:

    def __init__(self, bot):
        self.bot = bot
        self.mod_manager = ModerationManager(bot)

    async def mute(
        self,
        guild: discord.Guild,
        user: discord.Member,
        moderator: discord.Member,
        duration: Optional[int] = None,  
        reason: str = "Не указана",
        channel: Optional[discord.TextChannel] = None
    ) -> dict:

        if user.timed_out_until and user.timed_out_until > datetime.now(user.timed_out_until.tzinfo):
            remaining = user.timed_out_until - datetime.now(user.timed_out_until.tzinfo)
            remaining_formatted = _time.format_duration(int(remaining.total_seconds()))
            until_formatted = _time.format_datetime(user.timed_out_until)

            raise ModerationError(
                f"У пользователя уже есть мут до **{until_formatted}** (осталось {remaining_formatted})"
            )

        if not duration:
            raise ModerationError("Укажите длительность мута! Пример: `1h`, `30m`, `1d`")

        MAX_TIMEOUT_MINUTES = 28 * 24 * 60
        if duration > MAX_TIMEOUT_MINUTES:
            duration = MAX_TIMEOUT_MINUTES

        result = await self.mod_manager.execute(
            action_type=ActionType.MUTE,
            guild=guild,
            target=user,
            moderator=moderator,
            reason=reason,
            duration=duration,
            channel=channel
        )

        return result

    async def unmute(
        self,
        guild: discord.Guild,
        user: discord.Member,
        moderator: discord.Member,
        reason: str = "Не указана",
        channel: Optional[discord.TextChannel] = None
    ) -> dict:

        if not user.timed_out_until or user.timed_out_until <= datetime.now(user.timed_out_until.tzinfo):
            raise ModerationError("У пользователя нет активного мута!")

        active_mutes = await self.mod_manager.get_active_punishments(
            user_id=user.id,
            action_type=ActionType.MUTE
        )

        if not active_mutes:
            raise ModerationError("Мут найден в Discord, но не найден в БД!")

        punishment_rudiment = active_mutes[0]["rudiment"]

        result = await self.mod_manager.execute(
            action_type=ActionType.UNMUTE,
            guild=guild,
            target=user,
            moderator=moderator,
            reason=reason,
            channel=channel,
            punishment_rudiment=punishment_rudiment  
        )

        return result

