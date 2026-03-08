"""
QuestManager — управление прогрессом квестов.

Квесты рандомно выбираются из пула при каждом сбросе:
  - 3 ежедневных (сброс в 00:00 UTC)
  - 3 еженедельных (сброс в понедельник 00:00 UTC)

Таблица user_quests (Supabase):
    user_id, guild_id, quest_key  — UNIQUE
    progress, completed, reward_claimed
    started_at, completed_at, resets_at
"""

import random
import time as _pytime
from Niludetsu.database.supabase_database import SupabaseDatabase, database
from Niludetsu.economy.manager import EconomyManager
from Niludetsu.logging import logger
from Niludetsu.quests.definitions import (
    ALL_QUESTS,
    DAILY_POOL,
    DAILY_QUEST_COUNT,
    WEEKLY_POOL,
    WEEKLY_QUEST_COUNT,
    QuestDef,
    get_quest_by_key,
    total_pages,
)
from Niludetsu.tools.Time import TimeService
from typing import Any, Dict, List, Optional, Tuple

_time = TimeService()


class QuestProgress:
    """Прогресс одного квеста юзера."""

    __slots__ = ("quest", "progress", "completed", "reward_claimed", "resets_at")

    def __init__(
        self,
        quest: QuestDef,
        progress: int = 0,
        completed: bool = False,
        reward_claimed: bool = False,
        resets_at: str | None = None,
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
    """Управление квестами: рандомный выбор, прогресс, выдача наград."""

    def __init__(self, db: SupabaseDatabase | None = None):
        self.db = db or database
        self.economy = EconomyManager(self.db)
        # Кеш: "user_id:guild_id" -> timestamp последней проверки
        self._init_cache: Dict[str, float] = {}
        self._init_cache_ttl = 60  # секунд — не чекать если уже чекали < 60 сек назад

    # ——— utils ———

    def _next_daily_reset(self) -> str:
        """00:00 UTC следующего дня."""
        return _time.now().add(days=1).start_of("day").to_iso8601_string()

    def _next_weekly_reset(self) -> str:
        """Следующий понедельник 00:00 UTC."""
        now = _time.now()
        days_until_monday = (7 - now.day_of_week) % 7 or 7
        return now.add(days=days_until_monday).start_of("day").to_iso8601_string()

    def _next_reset(self, reset_type: str) -> str:
        if reset_type == "weekly":
            return self._next_weekly_reset()
        return self._next_daily_reset()

    def _is_expired(self, resets_at: str | None) -> bool:
        if not resets_at:
            return True
        reset_dt = _time.ensure_datetime(resets_at)
        if not reset_dt:
            return True
        return _time.now() >= reset_dt

    # ——— CRUD ———

    async def _get_quest_row(
        self, user_id: str, guild_id: str, quest_key: str
    ) -> Optional[Dict[str, Any]]:
        return await self.db.get_row(
            "user_quests",
            user_id=str(user_id),
            guild_id=str(guild_id),
            quest_key=quest_key,
        )

    async def _get_all_quest_rows(
        self, user_id: str, guild_id: str
    ) -> List[Dict[str, Any]]:
        return await self.db.get_rows(
            "user_quests",
            user_id=str(user_id),
            guild_id=str(guild_id),
        )

    async def _upsert_quest(
        self,
        user_id: str,
        guild_id: str,
        quest_key: str,
        payload: Dict[str, Any],
    ) -> None:
        base = {
            "user_id": str(user_id),
            "guild_id": str(guild_id),
            "quest_key": quest_key,
        }
        base.update(payload)

        try:
            await self.db.upsert(
                "user_quests",
                base,
                on_conflict="user_id,guild_id,quest_key",
            )
            return
        except Exception as exc:
            # Fallback для схем без UNIQUE(user_id, guild_id, quest_key).
            logger.warning(
                "Quest upsert fallback triggered (guild_id=%s, user_id=%s, quest_key=%s): %s",
                guild_id,
                user_id,
                quest_key,
                exc,
            )

        existing = await self._get_quest_row(user_id, guild_id, quest_key)
        if existing:
            await self._update_quest(user_id, guild_id, quest_key, payload)
        else:
            await self.db.insert("user_quests", base)

    async def _update_quest(
        self,
        user_id: str,
        guild_id: str,
        quest_key: str,
        values: Dict[str, Any],
    ) -> None:
        """Update уже существующего квеста (без upsert, без NOT NULL проблем)."""
        await self.db.update_record(
            "user_quests",
            where={
                "user_id": str(user_id),
                "guild_id": str(guild_id),
                "quest_key": quest_key,
            },
            values=values,
        )

    async def _delete_expired_quests(
        self, user_id: str, guild_id: str, reset_type: str
    ) -> None:
        """Удаляет истёкшие квесты данного типа."""
        rows = await self._get_all_quest_rows(user_id, guild_id)
        for row in rows:
            quest_def = get_quest_by_key(row["quest_key"])
            if not quest_def:
                # Квест из старого пула — удаляем
                await self.db.delete(
                    "user_quests",
                    user_id=str(user_id),
                    guild_id=str(guild_id),
                    quest_key=row["quest_key"],
                )
                continue
            if quest_def["reset"] == reset_type and self._is_expired(row.get("resets_at")):
                await self.db.delete(
                    "user_quests",
                    user_id=str(user_id),
                    guild_id=str(guild_id),
                    quest_key=row["quest_key"],
                )

    async def _roll_quests(
        self,
        user_id: str,
        guild_id: str,
        pool: List[QuestDef],
        count: int,
        reset_type: str,
    ) -> List[QuestDef]:
        """Рандомно выбирает квесты из пула и создаёт записи в БД."""
        selected = random.sample(pool, min(count, len(pool)))
        resets_at = self._next_reset(reset_type)

        for quest in selected:
            await self._upsert_quest(
                user_id,
                guild_id,
                quest["key"],
                {
                    "progress": 0,
                    "completed": False,
                    "reward_claimed": False,
                    "started_at": _time.now().to_iso8601_string(),
                    "completed_at": None,
                    "resets_at": resets_at,
                },
            )

        return selected

    # ——— public API ———

    async def get_user_quests(
        self, user_id: str, guild_id: str, page: int = 1
    ) -> List[QuestProgress]:
        """
        page=1: daily квесты
        page=2: weekly квесты

        Если квесты истекли/нет — рандомно выбирает новые.
        """
        reset_type = "daily" if page == 1 else "weekly"
        pool = DAILY_POOL if page == 1 else WEEKLY_POOL
        count = DAILY_QUEST_COUNT if page == 1 else WEEKLY_QUEST_COUNT

        # Получаем все записи юзера
        all_rows = await self._get_all_quest_rows(user_id, guild_id)

        # Фильтруем активные квесты нужного типа
        active: List[Dict[str, Any]] = []
        for row in all_rows:
            quest_def = get_quest_by_key(row["quest_key"])
            if not quest_def:
                continue
            if quest_def["reset"] != reset_type:
                continue
            if self._is_expired(row.get("resets_at")):
                continue
            active.append(row)

        # Если активных квестов мало — нужен ролл
        if len(active) < count:
            # Удаляем старые истёкшие
            await self._delete_expired_quests(user_id, guild_id, reset_type)
            # Роллим новые
            selected = await self._roll_quests(user_id, guild_id, pool, count, reset_type)
            # Перечитываем из БД
            all_rows = await self._get_all_quest_rows(user_id, guild_id)
            active = []
            for row in all_rows:
                quest_def = get_quest_by_key(row["quest_key"])
                if not quest_def:
                    continue
                if quest_def["reset"] != reset_type:
                    continue
                if self._is_expired(row.get("resets_at")):
                    continue
                active.append(row)

        # Строим результат
        result: List[QuestProgress] = []
        for row in active:
            quest_def = get_quest_by_key(row["quest_key"])
            if not quest_def:
                continue
            result.append(
                QuestProgress(
                    quest=quest_def,
                    progress=int(row.get("progress", 0)),
                    completed=bool(row.get("completed", False)),
                    reward_claimed=bool(row.get("reward_claimed", False)),
                    resets_at=row.get("resets_at"),
                )
            )

        return result

    async def _ensure_quests_exist(
        self, user_id: str, guild_id: str
    ) -> None:
        """
        Lazy init: если у юзера нет активных квестов — роллим.
        Вызывается из increment_progress чтобы прогресс считался
        даже если юзер ещё не открывал /quests.
        """
        cache_key = f"{user_id}:{guild_id}"
        now_ts = _pytime.time()

        # Пропускаем если недавно проверяли
        last_check = self._init_cache.get(cache_key, 0)
        if now_ts - last_check < self._init_cache_ttl:
            return

        all_rows = await self._get_all_quest_rows(user_id, guild_id)

        # Проверяем daily
        daily_active = [
            r for r in all_rows
            if get_quest_by_key(r["quest_key"])
            and get_quest_by_key(r["quest_key"])["reset"] == "daily"
            and not self._is_expired(r.get("resets_at"))
        ]
        if len(daily_active) < DAILY_QUEST_COUNT:
            await self._delete_expired_quests(user_id, guild_id, "daily")
            await self._roll_quests(user_id, guild_id, DAILY_POOL, DAILY_QUEST_COUNT, "daily")

        # Проверяем weekly
        weekly_active = [
            r for r in all_rows
            if get_quest_by_key(r["quest_key"])
            and get_quest_by_key(r["quest_key"])["reset"] == "weekly"
            and not self._is_expired(r.get("resets_at"))
        ]
        if len(weekly_active) < WEEKLY_QUEST_COUNT:
            await self._delete_expired_quests(user_id, guild_id, "weekly")
            await self._roll_quests(user_id, guild_id, WEEKLY_POOL, WEEKLY_QUEST_COUNT, "weekly")

        self._init_cache[cache_key] = now_ts

    async def increment_progress(
        self,
        user_id: str,
        guild_id: str,
        quest_type: str,
        amount: int = 1,
    ) -> None:
        """
        Инкрементирует прогресс по ВСЕМ активным квестам данного типа.
        Вызывается трекерами (сообщения, войс, бампы).

        Lazy init: если у юзера нет квестов — роллит автоматически.
        """
        # Гарантируем что квесты существуют
        await self._ensure_quests_exist(user_id, guild_id)

        all_rows = await self._get_all_quest_rows(user_id, guild_id)

        for row in all_rows:
            quest_def = get_quest_by_key(row["quest_key"])
            if not quest_def:
                continue
            if quest_def["type"] != quest_type:
                continue
            if self._is_expired(row.get("resets_at")):
                continue
            if row.get("completed"):
                continue

            new_progress = min(int(row.get("progress", 0)) + amount, quest_def["goal"])
            completed = new_progress >= quest_def["goal"]

            update: Dict[str, Any] = {"progress": new_progress, "completed": completed}
            if completed:
                update["completed_at"] = _time.now().to_iso8601_string()

            await self._update_quest(user_id, guild_id, quest_def["key"], update)

    async def claim_reward(
        self, user_id: str, guild_id: str, quest_key: str
    ) -> Tuple[bool, str]:
        """Забирает награду за квест."""
        quest_def = get_quest_by_key(quest_key)
        if not quest_def:
            return False, "Квест не найден"

        row = await self._get_quest_row(user_id, guild_id, quest_key)
        if not row:
            return False, "Квест не начат"

        if self._is_expired(row.get("resets_at")):
            return False, "Квест уже сброшен"

        if not row.get("completed"):
            return False, "Квест ещё не завершён"

        if row.get("reward_claimed"):
            return False, "Награда уже получена"

        # Выдаём монеты
        reward = quest_def["reward"]
        await self.economy.add_money(
            user_id, guild_id, reward, event="quest_reward",
            metadata={"quest": quest_key},
        )

        # Помечаем reward_claimed
        await self._update_quest(user_id, guild_id, quest_key, {"reward_claimed": True})

        return True, f"Получено **{reward:,}** монет за квест **{quest_def['name']}**!"

    async def get_claimable_quests(
        self, user_id: str, guild_id: str
    ) -> List[QuestProgress]:
        """Возвращает квесты, у которых можно забрать награду."""
        all_quests: List[QuestProgress] = []
        for page in range(1, total_pages() + 1):
            page_quests = await self.get_user_quests(user_id, guild_id, page)
            all_quests.extend(page_quests)
        return [q for q in all_quests if q.is_claimable]

