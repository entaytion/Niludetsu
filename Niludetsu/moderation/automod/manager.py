from __future__ import annotations

import time
from typing import Any

from ...database import database
from ...config import SERVERS
from .rules import AutoModRuleType, RuleConfig, AutoModRule, build_rule

MAIN_GUILD_ID = str(SERVERS["MAIN_ID"])


DEFAULT_RULES: dict[str, dict[str, Any]] = {
    AutoModRuleType.BAD_WORDS.value:     {"is_enabled": False, "whitelist": [], "ignored_channels": [], "action": "warn"},
    AutoModRuleType.CAPS_LOCK.value:     {"is_enabled": False, "whitelist": [], "ignored_channels": [], "action": "warn",  "limit": 70},
    AutoModRuleType.CUSTOM_WORDS.value:  {"is_enabled": False, "whitelist": [], "ignored_channels": [], "action": "warn"},
    AutoModRuleType.INVITES.value:       {"is_enabled": False, "whitelist": [], "ignored_channels": [], "action": "ban"},
    AutoModRuleType.LINKS.value:         {"is_enabled": False, "whitelist": [], "ignored_channels": [], "action": "warn"},
    AutoModRuleType.REPEATED_TEXT.value: {"is_enabled": False, "whitelist": [], "ignored_channels": [], "action": "warn", "limit": 5},
    AutoModRuleType.SPAM.value:          {"is_enabled": False, "whitelist": [], "ignored_channels": [], "action": "warn", "limit": 5},
}


def _to_config(data: dict[str, Any]) -> RuleConfig:
    return RuleConfig(
        is_enabled=data.get("is_enabled", False),
        whitelist=data.get("whitelist", []),
        ignored_channels=data.get("ignored_channels", []),
        action=data.get("action", "warn"),
        limit=data.get("limit", 5),
    )


class AutoModManager:

    _CACHE_TTL = 60.0

    def __init__(self, guild_id: str = MAIN_GUILD_ID) -> None:
        self.db = database
        self.guild_id = guild_id
        self._cache: dict[str, Any] | None = None
        self._cache_ts: float = 0.0


    def _is_stale(self) -> bool:
        return self._cache is None or (time.monotonic() - self._cache_ts) > self._CACHE_TTL

    def invalidate(self) -> None:
        self._cache = None
        self._cache_ts = 0.0

    async def _load(self) -> dict[str, Any]:
        row = await self.db.get_row("automoderation", guild_id=self.guild_id, key="settings")
        if row and row.get("value"):
            raw: dict = dict(row["value"])
            for k, v in DEFAULT_RULES.items():
                raw.setdefault(k, v.copy())
            self._cache = raw
        else:
            self._cache = DEFAULT_RULES.copy()
            await self._save(self._cache)
        self._cache_ts = time.monotonic()
        return self._cache

    async def _save(self, data: dict[str, Any]) -> bool:
        try:
            await self.db.upsert(
                "automoderation",
                {"guild_id": self.guild_id, "key": "settings", "value": data},
                on_conflict="guild_id",
            )
            return True
        except Exception as e:
            print(f"AutoMod save error: {e}")
            return False


    async def get_settings(self) -> dict[str, Any]:
        if self._is_stale():
            await self._load()
        return dict(self._cache)  # type: ignore[arg-type]

    async def get_rule(self, name: str) -> dict[str, Any]:
        s = await self.get_settings()
        return s.get(name, DEFAULT_RULES.get(name, {}))

    async def update_rule(self, name: str, data: dict[str, Any]) -> bool:
        s = await self.get_settings()
        s[name] = data
        self._cache = s
        return await self._save(s)

    async def toggle_rule(self, name: str) -> bool:
        rule = await self.get_rule(name)
        rule["is_enabled"] = not rule.get("is_enabled", False)
        await self.update_rule(name, rule)
        return rule["is_enabled"]

    async def add_ignored_channel(self, name: str, channel_id: str) -> bool:
        rule = await self.get_rule(name)
        channels = rule.setdefault("ignored_channels", [])
        if channel_id not in channels:
            channels.append(channel_id)
            return await self.update_rule(name, rule)
        return False

    async def remove_ignored_channel(self, name: str, channel_id: str) -> bool:
        rule = await self.get_rule(name)
        channels = rule.get("ignored_channels", [])
        if channel_id in channels:
            channels.remove(channel_id)
            return await self.update_rule(name, rule)
        return False

    async def get_enabled_rules(self) -> dict[str, Any]:
        s = await self.get_settings()
        return {k: v for k, v in s.items() if v.get("is_enabled")}


    async def build_active_rules(self) -> list[AutoModRule]:
        enabled = await self.get_enabled_rules()
        rules: list[AutoModRule] = []
        for key, data in enabled.items():
            try:
                rt = AutoModRuleType(key)
                rules.append(build_rule(rt, _to_config(data)))
            except (ValueError, KeyError):
                pass
        return rules
