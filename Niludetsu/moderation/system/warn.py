import discord
from Niludetsu.moderation.config import ActionType
from Niludetsu.moderation.exceptions import ModerationError
from Niludetsu.moderation.manager import ModerationManager
from typing import Optional

class WarnSystem:

    def __init__(self, bot):
        self.bot = bot
        self.mod_manager = ModerationManager(bot)

    async def add_warn(
        self,
        guild: discord.Guild,
        user: discord.Member,
        moderator: discord.Member,
        reason: str = "Не указана",
        duration: Optional[int] = None,  
        channel: Optional[discord.TextChannel] = None
    ) -> dict:
        result = await self.mod_manager.execute(
            action_type=ActionType.WARN,
            guild=guild,
            target=user,
            moderator=moderator,
            reason=reason,
            duration=duration,  
            channel=channel
        )

        return result

    async def remove_warn(
        self,
        guild: discord.Guild,
        user: discord.Member,
        warn_id: str,
        moderator: discord.Member,
        reason: str = "Не указана",
        channel: Optional[discord.TextChannel] = None
    ) -> dict:

        all_warns = await self.mod_manager.get_active_punishments(
            user_id=user.id,
            action_type=ActionType.WARN
        )

        target_warn = None
        for warn in all_warns:
            if warn.get("rudiment") == str(warn_id):
                target_warn = warn
                break

        if not target_warn:
            raise ModerationError(f"Предупреждение `#{warn_id}` не найдено!")

        if not target_warn.get("active"):
            raise ModerationError(f"Предупреждение `#{warn_id}` уже снято!")

        result = await self.mod_manager.execute(
            action_type=ActionType.UNWARN,
            guild=guild,
            target=user,
            moderator=moderator,
            reason=reason,
            channel=channel,
            punishment_rudiment=target_warn["rudiment"]  
        )

        return result

