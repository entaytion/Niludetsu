from ..tools.Time import TimeService

import asyncio
from typing import Dict, Tuple, Optional
from Niludetsu.database import database

_time = TimeService()

class LevelManager:

    def __init__(self) -> None:
        self.db = database

    @staticmethod
    def next_level_xp(level: int) -> int:
        return 5 * (level ** 2) + 50 * level + 100

    async def get_profile(self, guild_id: str, user_id: str) -> Dict[str, int]:
        user_data = await self.db.get_user(str(user_id), str(guild_id))
        profile = user_data["profile"]
        
        return {
            "level": int(profile.get("level", 1)),
            "experience": int(profile.get("experience", 0)),
            "reputation": int(profile.get("reputation", 0)),
        }

    async def add_experience(
        self,
        guild_id: str,
        user_id: str,
        amount: int,
    ) -> Tuple[Dict[str, int], bool]:
        if amount <= 0:
            return await self.get_profile(guild_id, user_id), False

        async with self.db.transaction() as conn:
            query_select = """
                SELECT level, experience, reputation 
                FROM public.user_profile 
                WHERE user_id = $1 AND guild_id = $2 
                FOR UPDATE
            """
            row = await conn.fetchrow(query_select, str(user_id), str(guild_id))
            
            if not row:
                return await self.get_profile(guild_id, user_id), False

            level = int(row["level"])
            exp = int(row["experience"]) + amount
            
            leveled_up = False
            new_level = level
            
            while exp >= (req := self.next_level_xp(new_level)):
                exp -= req
                new_level += 1
                leveled_up = True

            query_update = """
                UPDATE public.user_profile 
                SET level = $3, experience = $4, updated_at = now()
                WHERE user_id = $1 AND guild_id = $2
                RETURNING *
            """
            new_row = await conn.fetchrow(query_update, str(user_id), str(guild_id), new_level, exp)
            p = dict(new_row)
        
        await self.db.update_user_cache(str(user_id), str(guild_id), "profile", p)

        return {
            "level": p["level"],
            "experience": p["experience"],
            "reputation": p["reputation"]
        }, leveled_up

    async def adjust_reputation(self, guild_id: str, user_id: str, delta: int) -> Dict[str, int]:
        if delta == 0:
            return await self.get_profile(guild_id, user_id)

        new_profile = await self.db.increment_field(
            "user_profile",
            where={"user_id": str(user_id), "guild_id": str(guild_id)},
            field="reputation",
            amount=delta
        )
        
        if new_profile:
            await self.db.update_user_cache(str(user_id), str(guild_id), "profile", new_profile)
            return {
                "level": new_profile["level"],
                "experience": new_profile["experience"],
                "reputation": new_profile["reputation"]
            }
        
        return await self.get_profile(guild_id, user_id)
