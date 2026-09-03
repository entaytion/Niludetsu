from ..tools.Time import TimeService

import random
from typing import Any, Dict, List, Tuple, Optional

from Niludetsu.database import database
from Niludetsu.economy.manager import EconomyManager
from Niludetsu.quests.definitions import (
    DAILY_POOL,
    DAILY_QUEST_COUNT,
    WEEKLY_POOL,
    WEEKLY_QUEST_COUNT,
    QuestDef,
    get_quest_by_key,
)

_time = TimeService()

class QuestProgress:
    __slots__ = ("quest", "progress", "completed", "reward_claimed", "resets_at")

    def __init__(
        self,
        quest: QuestDef,
        progress: int = 0,
        completed: bool = False,
        reward_claimed: bool = False,
        resets_at: Any = None,
    ):
        self.quest = quest
        self.progress = progress
        self.completed = completed
        self.reward_claimed = reward_claimed
        self.resets_at = resets_at

    @property
    def is_claimable(self) -> bool:
        return self.completed and not self.reward_claimed

class QuestManager:

    def __init__(self, db=None):
        self.db = db or database
        self.economy = EconomyManager(self.db)

    def _next_reset(self, reset_type: str):
        now = _time.now()
        if reset_type == "weekly":
            days_until_monday = (7 - now.day_of_week) % 7 or 7
            return now.add(days=days_until_monday).start_of("day")
        return now.add(days=1).start_of("day")

    async def _ensure_active_quests(self, user_id: str, guild_id: str) -> List[Dict[str, Any]]:
        rows = await self.db.get_user_quests(user_id, guild_id)
        now = _time.now()
        
        active_rows = [r for r in rows if r["resets_at"] > now]
        
        daily = [r for r in active_rows if (q := get_quest_by_key(r["quest_key"])) and q["reset"] == "daily"]
        weekly = [r for r in active_rows if (q := get_quest_by_key(r["quest_key"])) and q["reset"] == "weekly"]

        to_add = []
        if len(daily) < DAILY_QUEST_COUNT:
            selected = random.sample(DAILY_POOL, DAILY_QUEST_COUNT)
            reset_at = self._next_reset("daily")
            for q in selected:
                to_add.append({
                    "user_id": str(user_id), "guild_id": str(guild_id), "quest_key": q["key"],
                    "progress": 0, "completed": False, "reward_claimed": False, "resets_at": reset_at
                })

        if len(weekly) < WEEKLY_QUEST_COUNT:
            selected = random.sample(WEEKLY_POOL, WEEKLY_QUEST_COUNT)
            reset_at = self._next_reset("weekly")
            for q in selected:
                to_add.append({
                    "user_id": str(user_id), "guild_id": str(guild_id), "quest_key": q["key"],
                    "progress": 0, "completed": False, "reward_claimed": False, "resets_at": reset_at
                })

        if to_add:
            await self.db._neon.execute(
                "DELETE FROM public.user_quests WHERE user_id = $1 AND guild_id = $2 AND resets_at <= $3",
                str(user_id), str(guild_id), now
            )
            await self.db.bulk_upsert_quests(to_add)
            return await self.db.get_user_quests(user_id, guild_id)
        
        return rows

    async def get_user_quests(self, user_id: str, guild_id: str, page: int = 1) -> List[QuestProgress]:
        rows = await self._ensure_active_quests(user_id, guild_id)
        reset_type = "daily" if page == 1 else "weekly"
        
        result = []
        for r in rows:
            q_def = get_quest_by_key(r["quest_key"])
            if q_def and q_def["reset"] == reset_type:
                result.append(QuestProgress(
                    quest=q_def, progress=r["progress"], completed=r["completed"],
                    reward_claimed=r["reward_claimed"], resets_at=r["resets_at"]
                ))
        return result

    async def increment_progress(self, user_id: str, guild_id: str, quest_type: str, amount: int = 1) -> None:
        rows = await self._ensure_active_quests(user_id, guild_id)
        
        target_quests = []
        for r in rows:
            q_def = get_quest_by_key(r["quest_key"])
            if q_def and q_def["type"] == quest_type and not r["completed"]:
                target_quests.append((r["quest_key"], q_def["goal"]))

        if not target_quests:
            return

        for q_key, goal in target_quests:
            query = """
                UPDATE public.user_quests 
                SET progress = LEAST(progress + $4, $5::int),
                    completed = (progress + $4 >= $5),
                    completed_at = CASE WHEN progress + $4 >= $5 THEN now() ELSE completed_at END
                WHERE user_id = $1 AND guild_id = $2 AND quest_key = $3 AND NOT completed
            """
            await self.db._neon.execute(query, str(user_id), str(guild_id), q_key, amount, goal)

    async def claim_reward(self, user_id: str, guild_id: str, quest_key: str) -> Tuple[bool, str]:
        query = """
            UPDATE public.user_quests 
            SET reward_claimed = true
            WHERE user_id = $1 AND guild_id = $2 AND quest_key = $3 
            AND completed AND NOT reward_claimed AND resets_at > now()
            RETURNING *
        """
        row = await self.db._neon.fetchrow(query, str(user_id), str(guild_id), quest_key)
        
        if not row:
            return False, "Квест не найден, не завершен или награда уже получена."

        q_def = get_quest_by_key(quest_key)
        await self.economy.add_money(user_id, guild_id, q_def["reward"], event="quest_reward")
        
        return True, f"Получено **{q_def['reward']:,}** монет за квест **{q_def['name']}**!"
