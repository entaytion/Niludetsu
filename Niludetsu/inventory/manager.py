from Niludetsu.database.supabase_database import SupabaseDatabase
from typing import Dict, List, Optional

class InventoryManager:
    def __init__(self, db: SupabaseDatabase):
        self.db = db

    async def get_items(self, user_id: str, guild_id: str) -> List[Dict]:
        return await self.db.fetch_inventory_items(user_id, guild_id)

    async def get_personal_role(self, user_id: str, guild_id: str) -> Optional[Dict]:
        items = await self.get_items(user_id, guild_id)
        role_item = next((item for item in items if item["item_type"] == "role"), None)
        if not role_item:
            return None
        return await self.db.fetch_owned_role(guild_id, role_item["item_key"])

