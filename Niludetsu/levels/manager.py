import asyncio
from Niludetsu.database.supabase_database import database
from Niludetsu.tools.Time import TimeService
from typing import Dict, Tuple

_time = TimeService()

class LevelManager:
    """Минимальный сервис для чтения/записи уровня и опыта."""

    def __init__(self) -> None:
        self.db = database
        self._locks: Dict[str, asyncio.Lock] = {}

    @staticmethod
    def next_level_xp(level: int) -> int:
        return 5 * (level ** 2) + 50 * level + 100

    def _lock_key(self, guild_id: str, user_id: str) -> str:
        return f"{guild_id}:{user_id}"

    def _get_lock(self, guild_id: str, user_id: str) -> asyncio.Lock:
        key = self._lock_key(guild_id, user_id)
        lock = self._locks.get(key)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[key] = lock
        return lock

    async def get_profile(self, guild_id: str, user_id: str) -> Dict[str, int]:
        await self.db.ensure_user(user_id, guild_id)
        row = await self.db.get_row(
            "user_profile",
            guild_id=str(guild_id),
            user_id=str(user_id),
        )
        if not row:
            return {"level": 1, "experience": 0, "reputation": 0}
        return {
            "level": int(row.get("level", 1)),
            "experience": int(row.get("experience", 0)),
            "reputation": int(row.get("reputation", 0)),
        }

    async def add_experience(
        self,
        guild_id: str,
        user_id: str,
        amount: int,
    ) -> Tuple[Dict[str, int], bool]:
        """Добавляет опыт и пересчитывает уровень. Возвращает профиль и флаг повышения уровня."""
        if amount <= 0:
            profile = await self.get_profile(guild_id, user_id)
            return profile, False

        await self.db.ensure_user(user_id, guild_id)
        lock = self._get_lock(guild_id, user_id)
        async with lock:
            row = await self.db.get_row(
                "user_profile",
                guild_id=str(guild_id),
                user_id=str(user_id),
            ) or {
                "level": 1,
                "experience": 0,
                "reputation": 0,
            }

            level = int(row.get("level", 1))
            exp = int(row.get("experience", 0))
            reputation = int(row.get("reputation", 0))

            exp += amount
            leveled_up = False
            while exp >= self.next_level_xp(level):
                exp -= self.next_level_xp(level)
                level += 1
                leveled_up = True

            updated = {
                "level": level,
                "experience": exp,
                "reputation": reputation,
                "updated_at": _time.now().to_iso8601_string(),
            }

            await self.db.update_record(
                "user_profile",
                where={
                    "user_id": str(user_id),
                    "guild_id": str(guild_id),
                },
                values=updated,
            )
            await self.db.invalidate_user_cache(str(user_id), str(guild_id))

            return {
                "level": level,
                "experience": exp,
                "reputation": reputation,
            }, leveled_up

    async def adjust_reputation(
        self,
        guild_id: str,
        user_id: str,
        delta: int,
    ) -> Dict[str, int]:
        """Изменяет репутацию и возвращает обновлённый профиль."""
        if delta == 0:
            return await self.get_profile(guild_id, user_id)

        await self.db.ensure_user(user_id, guild_id)
        lock = self._get_lock(guild_id, user_id)

        async with lock:
            row = await self.db.get_row(
                "user_profile",
                guild_id=str(guild_id),
                user_id=str(user_id),
            ) or {
                "level": 1,
                "experience": 0,
                "reputation": 0,
            }

            level = int(row.get("level", 1))
            exp = int(row.get("experience", 0))
            reputation = int(row.get("reputation", 0)) + delta

            updated = {
                "level": level,
                "experience": exp,
                "reputation": reputation,
                "updated_at": _time.now().to_iso8601_string(),
            }

            await self.db.update_record(
                "user_profile",
                where={
                    "user_id": str(user_id),
                    "guild_id": str(guild_id),
                },
                values=updated,
            )
            await self.db.invalidate_user_cache(str(user_id), str(guild_id))

            return {
                "level": level,
                "experience": exp,
                "reputation": reputation,
            }

