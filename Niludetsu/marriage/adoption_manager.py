from Niludetsu.database.supabase_database import database
from Niludetsu.marriage.marriage_manager import MarriageManager
from typing import List, Dict, Optional, Any

class AdoptionManager:
    def __init__(self, db=database, marriage_manager: Optional[MarriageManager] = None):
        self.db = db
        self.marriage_manager = marriage_manager or MarriageManager(db)

    async def is_child_elsewhere(self, guild_id: str, user_id: str) -> bool:
        rows = await self.db.where(
            "user_marriages",
            filters=[
                {"column": "guild_id", "value": str(guild_id)},
                {"column": "status", "value": "active"},
            ],
        )
        for marriage in rows:
            kids = await self.db.fetch_children(marriage["id"])
            if any(str(k["user_id"]) == str(user_id) for k in kids):
                return True
        return False

    async def add_child(
        self,
        guild_id: str,
        parent_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        marriage = await self.marriage_manager.fetch_marriage(guild_id, parent_id)
        if not marriage:
            raise RuntimeError("no_marriage")
        if await self.is_child_elsewhere(guild_id, user_id):
            raise RuntimeError("already_child")
        return await self.marriage_manager.add_child(marriage["id"], user_id)

    async def remove_child(self, guild_id: str, parent_id: str, user_id: str) -> None:
        marriage = await self.marriage_manager.fetch_marriage(guild_id, parent_id)
        if not marriage:
            raise RuntimeError("no_marriage")
        await self.marriage_manager.remove_child(marriage["id"], user_id)

