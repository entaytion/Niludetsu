from Niludetsu.database import database
from Niludetsu.economy.manager import EconomyManager
from typing import Optional, Dict, List, Any

class MarriageManager:

    def __init__(self, db=None):
        self.db = db or database
        self.economy = EconomyManager(self.db)

    async def fetch_marriage(self, guild_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        return await self.db.get_active_marriage(str(guild_id), str(user_id))

    async def create_marriage(self, guild_id: str, proposer_id: str, partner_id: str) -> Dict[str, Any]:
        for uid in (proposer_id, partner_id):
            if await self.fetch_marriage(guild_id, uid):
                raise RuntimeError(f"User {uid} is already married")

        return await self.db.ensure_record(
            "user_marriages",
            guild_id=str(guild_id),
            partner_a_id=str(proposer_id),
            partner_b_id=str(partner_id),
            status="active"
        )

    async def sync_spousal_flags(self, guild_id: str, marriage: Dict[str, Any], *, enabled: bool) -> None:
        uids = [marriage["partner_a_id"], marriage["partner_b_id"]]
        payload = [{"user_id": uid, "guild_id": str(guild_id), "spousal_enabled": enabled} for uid in uids]
        
        await self.db.upsert("user_economy", payload, on_conflict="user_id,guild_id")
        for uid in uids:
            await self.db.invalidate_user_cache(uid, str(guild_id))

    async def unify_spousal_balance(self, guild_id: str, marriage: Dict[str, Any]) -> int:
        acc_a = await self.economy.get_account(marriage["partner_a_id"], guild_id)
        acc_b = await self.economy.get_account(marriage["partner_b_id"], guild_id)
        
        value = max(acc_a["spousal_balance"], acc_b["spousal_balance"])
        uids = [marriage["partner_a_id"], marriage["partner_b_id"]]
        
        payload = [{"user_id": uid, "guild_id": str(guild_id), "spousal_balance": value} for uid in uids]
        await self.db.upsert("user_economy", payload, on_conflict="user_id,guild_id")
        
        for uid in uids:
            await self.db.invalidate_user_cache(uid, str(guild_id))
        return value

    async def clear_spousal_balance(self, guild_id: str, marriage: Dict[str, Any]) -> int:
        value = await self.unify_spousal_balance(guild_id, marriage)
        uids = [marriage["partner_a_id"], marriage["partner_b_id"]]
        
        payload = [{"user_id": uid, "guild_id": str(guild_id), "spousal_balance": 0} for uid in uids]
        await self.db.upsert("user_economy", payload, on_conflict="user_id,guild_id")
        
        for uid in uids:
            await self.db.invalidate_user_cache(uid, str(guild_id))
        return value

    async def add_child(self, marriage_id: str, user_id: str) -> Dict[str, Any]:
        return await self.db.ensure_record("user_marriage_children", marriage_id=marriage_id, user_id=str(user_id))

    async def fetch_children(self, marriage_id: str) -> List[Dict[str, Any]]:
        return await self.db.get_rows("user_marriage_children", marriage_id=marriage_id)

    async def remove_child(self, marriage_id: str, user_id: str) -> None:
        await self.db.delete("user_marriage_children", marriage_id=marriage_id, user_id=str(user_id))
