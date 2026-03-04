import discord
from Niludetsu.achievements.config import ACHIEVEMENTS
from Niludetsu.database.supabase_database import database
from Niludetsu.economy.manager import EconomyManager
from Niludetsu.tools.Embed import Embed, Colors
from Niludetsu.tools.Emojis import Emojis
from Niludetsu.tools.Time import TimeService
from typing import Dict, Iterable, List, Optional, Set

class AchievementsManager:
    def __init__(self):
        self.db = database
        self.economy = EconomyManager(self.db)
        self.time = TimeService()

    def list_definitions(self) -> Dict[str, Dict]:
        return ACHIEVEMENTS

    async def has_achievement(self, guild_id: str, user_id: str, achievement_id: str) -> bool:
        existing = await self.db.get_row(
            "user_achievements",
            guild_id=str(guild_id),
            user_id=str(user_id),
            achievement_id=str(achievement_id),
        )
        return existing is not None

    async def unlock(
        self,
        guild_id: str,
        user_id: str,
        achievement_id: str,
        *,
        channel: Optional[discord.abc.Messageable] = None,
        metadata: Optional[Dict] = None,
        existing: Optional[Set[str]] = None,
    ) -> bool:
        data = ACHIEVEMENTS.get(achievement_id)
        if not data:
            return False

        if existing is not None:
            if achievement_id in existing:
                return False
        else:
            already = await self.has_achievement(guild_id, user_id, achievement_id)
            if already:
                return False

        # Переконуємося, що користувач існує в таблиці users
        await self.db.ensure_user(user_id, guild_id)

        record = await self.db.ensure_achievement(
            guild_id,
            user_id,
            achievement_id,
            metadata=metadata,
        )

        if existing is not None:
            existing.add(achievement_id)

        await self.db.update_record(
            "user_economy",
            {"user_id": str(user_id), "guild_id": str(guild_id)},
            {"spousal_balance": None},  # небольшая no-op чтобы ensure_user проглотил
        )

        await self.economy.add_money(
            user_id,
            guild_id,
            data["reward"],
            share_spousal=True,
        )

        if channel:
            embed = Embed(
                title=f"{data['icon']} Новое достижение!",
                description=(
                    f"<@{user_id}> получил достижение **{data['name']}**\n"
                    f"Награда: **``{data['reward']:,}``** {Emojis.MONEY}"
                ),
                color=Colors.PRIMARY,
            )
            embed.set_footer(text=self.time.format_datetime(record["unlocked_at"]))
            await channel.send(embed=embed)

        return True

    async def get_user_summary(self, guild_id: str, user_id: str) -> Dict[str, Dict]:
        rows = await self.db.list_achievements(guild_id, user_id)
        summary = {}
        for ach_id, definition in ACHIEVEMENTS.items():
            unlocked = next(
                (row for row in rows if row["achievement_id"] == ach_id),
                None,
            )
            summary[ach_id] = {
                **definition,
                "unlocked": unlocked is not None,
                "unlocked_at": unlocked["unlocked_at"] if unlocked else None,
                "metadata": unlocked["metadata"] if unlocked else {},
            }
        return summary

    async def check_and_unlock(
        self,
        guild_id: str,
        user_id: str,
        achievement_id: str,
        *,
        channel: Optional[discord.abc.Messageable] = None,
        metadata: Optional[Dict] = None,
    ) -> bool:
        """
        Проверяет и разблокирует достижение, если оно ещё не получено.

        Args:
            guild_id: ID гильдии
            user_id: ID пользователя
            achievement_id: ID достижения
            channel: Канал для уведомления
            metadata: Метаданные

        Returns:
            True если достижение было разблокировано
        """
        already_unlocked = await self.has_achievement(guild_id, user_id, achievement_id)
        if already_unlocked:
            return False

        return await self.unlock(
            guild_id,
            user_id,
            achievement_id,
            channel=channel,
            metadata=metadata,
        )

    async def evaluate_requirements(
        self,
        guild_id: str,
        user_id: str,
        *,
        channel: Optional[discord.abc.Messageable] = None,
        stats: Optional[Dict] = None,
        profile: Optional[Dict] = None,
        achievement_ids: Optional[Iterable[str]] = None,
    ) -> List[str]:
        candidates = (
            {ach_id: ACHIEVEMENTS[ach_id] for ach_id in achievement_ids if ach_id in ACHIEVEMENTS}
            if achievement_ids
            else ACHIEVEMENTS
        )

        if not candidates:
            return []

        existing_rows = await self.db.list_achievements(guild_id, user_id)
        unlocked_ids: Set[str] = {row["achievement_id"] for row in existing_rows}

        required_keys: Set[str] = set()
        for data in candidates.values():
            requirements = data.get("requirements") or {}
            required_keys.update(requirements.keys())

        need_stats = any(key in {"messages_clean", "voice_hours"} for key in required_keys)
        need_profile = "level" in required_keys

        if stats is None and need_stats:
            from Niludetsu.analytics.manager import AnalyticsManager

            stats = await AnalyticsManager().get_user_stats(guild_id, user_id)

        if profile is None and need_profile:
            from Niludetsu.levels.manager import LevelManager

            profile = await LevelManager().get_profile(guild_id, user_id)

        metrics: Dict[str, float] = {}
        if stats is not None:
            total_messages = stats.get("messages", {}).get("total", 0)
            deleted_messages = stats.get("messages", {}).get("deleted", 0)
            metrics["messages_clean"] = max(0, int(total_messages) - int(deleted_messages))
            metrics["voice_hours"] = stats.get("voice", {}).get("total_seconds", 0) / 3600

        if profile is not None:
            metrics["level"] = int(profile.get("level", 0))

        newly_unlocked: List[str] = []

        for achievement_id, data in candidates.items():
            if achievement_id in unlocked_ids:
                continue

            requirements = data.get("requirements") or {}
            if not requirements:
                continue

            meets_all = True
            for key, threshold in requirements.items():
                value = metrics.get(key)
                if value is None or value < threshold:
                    meets_all = False
                    break

            if not meets_all:
                continue

            unlocked = await self.unlock(
                guild_id,
                user_id,
                achievement_id,
                channel=channel,
                metadata=None,
                existing=unlocked_ids,
            )

            if unlocked:
                newly_unlocked.append(achievement_id)

        return newly_unlocked

