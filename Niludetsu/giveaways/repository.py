from ..tools.Time import TimeService

from Niludetsu.database import Database

from typing import List, Optional, Dict, Any

_time = TimeService()

class GiveawayRepository:
    def __init__(self, db: Database):
        self.db = db

    async def create_giveaway(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        payload = payload.copy()
        payload.setdefault("is_ended", False)
        return await self.db.insert("giveaways", payload)

    async def update_giveaway(self, giveaway_id: int, values: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        values = values.copy()
        return await self.db.update_record(
            "giveaways",
            {"giveaway_id": giveaway_id},
            values,
            ensure_if_missing=False,
        )

    async def get_active(self, guild_id: str) -> List[Dict[str, Any]]:
        return await self.db.where(
            "giveaways",
            filters=[
                {"column": "guild_id", "value": guild_id},
                {"column": "is_ended", "value": False},
            ],
        )

    async def get_due(self) -> List[Dict[str, Any]]:
        asap = _time.now()
        return await self.db.where(
            "giveaways",
            filters=[
                {"column": "is_ended", "value": False},
                {"op": "lte", "column": "end_time", "value": asap},
            ],
        )

    async def fetch_one(self, giveaway_id: int) -> Optional[Dict[str, Any]]:
        return await self.db.get_row("giveaways", giveaway_id=giveaway_id)

    async def upsert_participant(self, giveaway_id: int, user_id: str, *, left: bool = False, no_rejoin: bool = False):
        payload = {
            "giveaway_id": giveaway_id,
            "user_id": user_id,
            "joined_at": _time.now(),
            "left_at": _time.now() if left else None,
            "no_rejoin": no_rejoin,
        }
        return await self.db.upsert(
            "giveaway_participants",
            payload,
            on_conflict="giveaway_id,user_id",
        )

    async def remove_participant(self, giveaway_id: int, user_id: str):
        return await self.db.delete("giveaway_participants", giveaway_id=giveaway_id, user_id=user_id)

    async def list_participants(self, giveaway_id: int, *, active_only: bool = True) -> List[str]:
        filters = [{"column": "giveaway_id", "value": giveaway_id}]
        if active_only:
            filters.append({"op": "is", "column": "left_at", "value": None})
        rows = await self.db.where(
            "giveaway_participants",
            filters=filters,
            columns=["user_id"],
        )
        return [row["user_id"] for row in rows]

