from Niludetsu.database.supabase_database import database
from typing import Optional

class TempRoomsRepository:
    def __init__(self) -> None:
        self.db = database

    async def get_room_row(self, channel_id: str) -> Optional[dict]:
        return await self.db.get_row(
            "temprooms",
            channel_id=str(channel_id),
        )

    async def is_temp_channel(self, channel_id: str) -> bool:
        try:
            row = await self.get_room_row(channel_id)
        except Exception:
            return False
        return row is not None

    async def ensure_room(
        self,
        *,
        channel_id: str,
        guild_id: str,
        owner_id: str,
        name: Optional[str] = None,
    ) -> dict:
        return await self.db.ensure_record(
            "temprooms",
            channel_id=str(channel_id),
            guild_id=str(guild_id),
            owner_id=str(owner_id),
            name=name or "🔊 {name}",
            active=True,
        )

    async def update_room(self, channel_id: str, **fields) -> None:
        if not fields:
            return
        await self.db.update_record(
            "temprooms",
            {"channel_id": str(channel_id)},
            fields,
        )

    async def deactivate_room(self, channel_id: str) -> None:
        await self.update_room(channel_id, active=False, thread_id=None)

