from Niludetsu.database.supabase_database import database
from Niludetsu.economy.manager import EconomyManager
from typing import Optional, Dict, List, Any

class MarriageManager:
    def __init__(self, db=database):
        self.db = db
        self.economy = EconomyManager(db)

    async def ensure_single(self, user_id: str, guild_id: str) -> None:
        marriage = await self.db.get_active_marriage(guild_id, user_id)
        if marriage and marriage["status"] == "active":
            raise RuntimeError("already_married")

    async def create_marriage(
        self,
        guild_id: str,
        proposer_id: str,
        partner_id: str,
    ) -> Dict[str, Any]:
        await self.ensure_single(proposer_id, guild_id)
        await self.ensure_single(partner_id, guild_id)
        data = await self.db.ensure_marriage_record(
            guild_id,
            proposer_id,
            partner_id,
            metadata={"created_by": proposer_id},
        )
        return data

    async def finish_marriage(
        self,
        marriage_id: str,
        *,
        status: str,
    ) -> None:
        await self.db.close_marriage(marriage_id, status=status)

    async def fetch_marriage(self, guild_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        return await self.db.get_active_marriage(guild_id, user_id)

    async def children(self, marriage_id: str) -> List[Dict[str, Any]]:
        return await self.db.fetch_children(marriage_id)

    async def add_child(self, marriage_id: str, user_id: str) -> Dict[str, Any]:
        return await self.db.add_child(marriage_id, user_id)

    async def remove_child(self, marriage_id: str, user_id: str) -> None:
        await self.db.remove_child(marriage_id, user_id)

    async def sync_spousal_flags(self, guild_id: str, marriage: Dict[str, Any], *, enabled: bool) -> None:
        for user_id in (marriage["partner_a_id"], marriage["partner_b_id"]):
            await self.db.update_record(
                "user_economy",
                {"user_id": user_id, "guild_id": guild_id},
                {"spousal_enabled": enabled},
            )

    async def unify_spousal_balance(self, guild_id: str, marriage: Dict[str, Any]) -> int:
        """Возвращает актуальный семейный баланс и выравнивает его у обоих партнёров."""
        a = await self.economy.get_spousal_balance(marriage["partner_a_id"], guild_id)
        b = await self.economy.get_spousal_balance(marriage["partner_b_id"], guild_id)
        value = max(a, b)
        for user_id in (marriage["partner_a_id"], marriage["partner_b_id"]):
            await self.db.update_economy(
                user_id,
                guild_id,
                {"spousal_balance": value},
                json_fields=[],
            )
        return value

    async def clear_spousal_balance(self, guild_id: str, marriage: Dict[str, Any]) -> int:
        value = await self.unify_spousal_balance(guild_id, marriage)
        for user_id in (marriage["partner_a_id"], marriage["partner_b_id"]):
            await self.db.update_record(
                "user_economy",
                {"user_id": user_id, "guild_id": guild_id},
                {"spousal_balance": 0},
            )
        return value

