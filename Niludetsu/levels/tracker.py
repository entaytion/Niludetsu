from __future__ import annotations

from ..tools.Embed import Embed
from ..tools.Time import TimeService

"""
Трекер уровней — начисляет опыт за активность. Динамические настройки из БД.
"""
import time
import random
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, Any

from Niludetsu.achievements.manager import AchievementsManager
from Niludetsu.analytics.manager import AnalyticsManager
from Niludetsu.levels.manager import LevelManager

_time = TimeService()

@dataclass
class TrackerCooldowns:
    message_xp: Dict[str, datetime]
    level_notification: Dict[str, datetime]

class LevelTracker:

    LEVEL_ACHIEVEMENTS = ("level_five", "level_ten", "level_twenty", "level_fifty")
    VOICE_ACHIEVEMENTS = ("voice_hour", "voice_ten_hours", "voice_hundred_hours")

    DEFAULT_CONFIG = {
        "xp_per_message": [10, 25],
        "xp_per_voice_minute": 5,
        "message_cooldown": 60,
        "excluded_categories": [1363075274018914354]
    }

    _CONFIG_TTL = 60
    def __init__(self, main_guild_id: Optional[int] = None, config_manager=None):
        self.manager = LevelManager()
        self.analytics = AnalyticsManager()
        self.achievements = AchievementsManager()
        self.main_guild_id = main_guild_id
        self.config_manager = config_manager

        self._cooldowns = TrackerCooldowns(message_xp={}, level_notification={})
        self._cached_config: Optional[Dict[str, Any]] = None
        self._config_fetched_at: float = 0.0

    async def get_config(self) -> Dict[str, Any]:
        now = time.monotonic()
        if self._cached_config is not None and (now - self._config_fetched_at) < self._CONFIG_TTL:
            return self._cached_config
        self._cached_config = await self.manager.db.get_settings("levels_config", self.DEFAULT_CONFIG)
        self._config_fetched_at = now
        return self._cached_config

    async def track_message_xp(self, guild_id: str, user_id: str, channel) -> Optional[Dict]:
        if not self._is_main_guild(guild_id):
            return None

        config = await self.get_config()
        if self._is_excluded_channel(channel, config):
            return None

        now = _time.now()
        last_xp = self._cooldowns.message_xp.get(user_id)
        cooldown = self._config_value(config, "message_cooldown")
        if self._is_cooldown_active(last_xp, now, cooldown):
            return None

        self._cooldowns.message_xp[user_id] = now
        xp_range = self._config_value(config, "xp_per_message")
        xp_amount = random.randint(xp_range[0], xp_range[1])

        return await self._apply_xp(guild_id, user_id, xp_amount, channel=channel, is_voice=False)

    async def track_voice_xp(self, guild_id: str, user_id: str, minutes: int, channel) -> Optional[Dict]:
        if minutes <= 0 or not self._is_main_guild(guild_id):
            return None

        config = await self.get_config()
        xp_per_min = self._config_value(config, "xp_per_voice_minute")
        xp_amount = minutes * xp_per_min
        result = await self._apply_xp(guild_id, user_id, xp_amount, channel=channel, is_voice=True)

        stats = await self.analytics.get_user_stats(guild_id, user_id)
        await self.achievements.evaluate_requirements(guild_id, user_id, channel=channel, stats=stats, achievement_ids=self.VOICE_ACHIEVEMENTS)

        return result

    def _is_excluded_channel(self, channel, config: Dict) -> bool:
        if not hasattr(channel, "guild") or not channel.guild:
            return True

        excluded = self._config_value(config, "excluded_categories")
        if hasattr(channel, "category") and channel.category and channel.category.id in excluded:
            return True

        return False

    async def _send_levelup_notification(self, channel, user_id: str, new_level: int, is_voice: bool = False, xp: int = 0):
        now = _time.now()
        previous = self._cooldowns.level_notification.get(user_id)
        if self._is_cooldown_active(previous, now, 60):
            return
        self._cooldowns.level_notification[user_id] = now

        guild_id = channel.guild.id if hasattr(channel, "guild") and channel.guild else None
        if guild_id and self.config_manager:
            custom = self.config_manager.get_custom_embed(
                guild_id, "levels", "level_up_embed",
                user_mention=f"<@{user_id}>",
                level=new_level,
                xp=str(xp),
            )
            if custom:
                await channel.send(embed=Embed(**custom))
                return
            custom_text = self.config_manager.get_custom_text(
                guild_id, "levels", "level_up_message",
                user_mention=f"<@{user_id}>",
                level=new_level,
                xp=str(xp),
            )
            if custom_text:
                await channel.send(embed=Embed.default(description=custom_text))
                return

        from Niludetsu.locale import DEFAULT_LOCALE
        base = DEFAULT_LOCALE.get("levels", {}).get("level_up_message", "{user_mention}, у вас теперь **{level}** уровень!")
        suffix = DEFAULT_LOCALE.get("levels", {}).get("level_up_voice", "") if is_voice else DEFAULT_LOCALE.get("levels", {}).get("level_up_chat", "")
        msg = base.format(user_mention=f"<@{user_id}>", level=new_level) + suffix
        await channel.send(embed=Embed.default(description=msg))

    def _is_main_guild(self, guild_id: str | int) -> bool:
        return not self.main_guild_id or int(guild_id) == self.main_guild_id

    def _config_value(self, config: Dict[str, Any], key: str) -> Any:
        return config.get(key, self.DEFAULT_CONFIG[key])

    def _is_cooldown_active(
        self,
        previous: Optional[datetime],
        now: datetime,
        cooldown_seconds: int,
    ) -> bool:
        return bool(previous and (now - previous).total_seconds() < cooldown_seconds)

    async def _apply_xp(
        self,
        guild_id: str,
        user_id: str,
        xp_amount: int,
        *,
        channel,
        is_voice: bool,
    ) -> Dict[str, Any]:
        profile, leveled_up = await self.manager.add_experience(guild_id, user_id, xp_amount)

        if leveled_up:
            await self._send_levelup_notification(channel, user_id, profile["level"], is_voice=is_voice, xp=profile["experience"])
            await self.achievements.evaluate_requirements(
                guild_id,
                user_id,
                channel=channel,
                profile=profile,
                achievement_ids=self.LEVEL_ACHIEVEMENTS,
            )

        return {"profile": profile, "leveled_up": leveled_up}
