from __future__ import annotations

from typing import Any

from .base import BaseMixin


class QuestsMixin(BaseMixin):
    async def get_user_quests(self, user_id: str, guild_id: str) -> list[dict[str, Any]]:
        return await self.get_rows("user_quests", user_id=str(user_id), guild_id=str(guild_id))

    async def bulk_upsert_quests(self, payload: list[dict[str, Any]]) -> None:
        if not payload:
            return
        await self.upsert("user_quests", payload, on_conflict="user_id,guild_id,quest_key")

    async def delete_quests(self, user_id: str, guild_id: str, quest_keys: list[str]) -> None:
        if not quest_keys:
            return
        await self._neon.execute(
            "DELETE FROM public.user_quests WHERE user_id = $1 AND guild_id = $2 AND quest_key = ANY($3)",
            str(user_id),
            str(guild_id),
            quest_keys,
        )
