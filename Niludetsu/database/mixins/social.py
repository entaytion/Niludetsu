from __future__ import annotations
from ...tools.Time import TimeService

from typing import Any, Optional

from .base import BaseMixin

_time = TimeService()

class SocialMixin(BaseMixin):
    async def get_active_marriage(self, guild_id: str, user_id: str) -> Optional[dict[str, Any]]:
        query = """
            SELECT * FROM public.user_marriages
            WHERE guild_id = $1
            AND status = 'active'
            AND (partner_a_id = $2 OR partner_b_id = $2)
            LIMIT 1
        """
        row = await self._neon.fetchrow(query, str(guild_id), str(user_id))
        return dict(row) if row else None

    async def ensure_marriage_record(
        self, guild_id: str, partner_a_id: str, partner_b_id: str, **kwargs: Any
    ) -> dict[str, Any]:
        return await self.ensure_record(
            "user_marriages",
            guild_id=guild_id,
            partner_a_id=partner_a_id,
            partner_b_id=partner_b_id,
            **kwargs,
        )

    async def close_marriage(self, marriage_id: str, *, status: str = "divorced") -> None:
        await self.update_record(
            "user_marriages",
            {"id": marriage_id},
            {"status": status, "metadata": {"closed_at": _time.now()}},
            json_fields=["metadata"],
        )

    async def get_marriage_partner(self, marriage: dict[str, Any], user_id: str) -> str:
        if str(marriage["partner_a_id"]) == str(user_id):
            return marriage["partner_b_id"]
        return marriage["partner_a_id"]

    async def list_achievements(self, guild_id: str, user_id: str) -> list[dict[str, Any]]:
        return await self.get_rows("user_achievements", guild_id=str(guild_id), user_id=str(user_id))

    async def ensure_achievement(
        self, guild_id: str, user_id: str, achievement_id: str, **kwargs: Any
    ) -> dict[str, Any]:
        return await self.ensure_record(
            "user_achievements",
            guild_id=guild_id,
            user_id=user_id,
            achievement_id=achievement_id,
            **kwargs,
        )
