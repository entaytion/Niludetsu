import discord
from ..tools.Time import TimeService

from Niludetsu.achievements.config import ACHIEVEMENTS
from Niludetsu.database import database
from Niludetsu.economy.manager import EconomyManager

from Niludetsu.embeds.Achievements import AchievementEmbed
from typing import Dict, Iterable, List, Optional, Set

class AchievementsManager:
    
    def __init__(self):
        self.db = database
        self.economy = EconomyManager(self.db)
        self.time = TimeService()

    def list_definitions(self) -> Dict[str, Dict]:
        return ACHIEVEMENTS

    async def get_user_summary(self, guild_id: str, user_id: str) -> Dict[str, Dict]:
        existing_rows = await self.db.list_achievements(guild_id, user_id)
        unlocked_ids = {row["achievement_id"] for row in existing_rows}

        summary = {}
        for aid, data in ACHIEVEMENTS.items():
            summary[aid] = {
                **data,
                "unlocked": aid in unlocked_ids
            }
        return summary

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
        user: Optional[discord.Member | discord.User] = None,
        metadata: Optional[Dict] = None,
        existing: Optional[Set[str]] = None,
        send_embed: bool = True,
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

        record = await self.db.ensure_record(
            "user_achievements",
            guild_id=str(guild_id),
            user_id=str(user_id),
            achievement_id=str(achievement_id),
            metadata=metadata or {},
        )

        if existing is not None:
            existing.add(achievement_id)

        await self.economy.add_money(
            user_id,
            guild_id,
            data["reward"],
            event=f"achievement_{achievement_id}",
            share_spousal=True,
        )

        await self.db.invalidate_user_cache(str(user_id), str(guild_id))

        if channel and send_embed:
            if not user:
                if hasattr(channel, "guild"):
                    user = channel.guild.get_member(int(user_id)) or await channel.guild.fetch_member(int(user_id))
                else:
                    user = await channel.bot.fetch_user(int(user_id))
            
            if user:
                embed = AchievementEmbed.unlocked(user, [data])
                await channel.send(embed=embed)

        return True

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

        metrics: Dict[str, float] = {}
        if stats:
            total = stats.get("messages", {}).get("total", 0)
            deleted = stats.get("messages", {}).get("deleted", 0)
            metrics["messages_clean"] = max(0, int(total) - int(deleted))
            metrics["voice_hours"] = stats.get("voice", {}).get("total_seconds", 0) / 3600

        if profile:
            metrics["level"] = int(profile.get("level", 0))

        newly_unlocked: List[str] = []
        newly_unlocked_data: List[Dict] = []

        for achievement_id, data in candidates.items():
            if achievement_id in unlocked_ids:
                continue

            requirements = data.get("requirements") or {}
            if not requirements:
                continue

            if all(metrics.get(k, 0) >= v for k, v in requirements.items()):
                if await self.unlock(guild_id, user_id, achievement_id, send_embed=False):
                    newly_unlocked.append(achievement_id)
                    newly_unlocked_data.append(data)

        if newly_unlocked_data and channel:
            user_obj = None
            if hasattr(channel, "guild"):
                user_obj = channel.guild.get_member(int(user_id)) or await channel.guild.fetch_member(int(user_id))
            
            if user_obj:
                embed = AchievementEmbed.unlocked(user_obj, newly_unlocked_data)
                await channel.send(embed=embed)

        return newly_unlocked
