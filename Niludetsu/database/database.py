from __future__ import annotations
from ..tools.Time import TimeService

import asyncio
import json
import time
from typing import Any, Optional

from loguru import logger

from .mixins.base import BaseMixin
from .mixins.economy import EconomyMixin
from .mixins.social import SocialMixin
from .mixins.analytics import AnalyticsMixin
from .mixins.quests import QuestsMixin
from .mixins.shop import ShopMixin

_time = TimeService()

class Database(EconomyMixin, SocialMixin, AnalyticsMixin, QuestsMixin, ShopMixin, BaseMixin):
    def __init__(self):
        super().__init__()
        self._user_cache: dict[str, Any] = {}
        self._cache_ttl = 300
        self._cache_lock = asyncio.Lock()

    def _ensure_dict(self, data: Any) -> dict[str, Any]:
        if isinstance(data, dict):
            return data
        if isinstance(data, str):
            try:
                import json
                return json.loads(data)
            except Exception:
                return {}
        return {}

    async def get_user(self, user_id: str, guild_id: str) -> dict[str, Any]:
        key = f"{user_id}:{guild_id}"
        async with self._cache_lock:
            cached = self._user_cache.get(key)
            if cached and (time.time() - cached[1] < self._cache_ttl):
                return cached[0]

        select_query = """
            SELECT 
                to_jsonb(u.*) as core,
                to_jsonb(e.*) as economy,
                to_jsonb(p.*) as profile,
                to_jsonb(a.*) as analytics,
                (SELECT to_jsonb(m.*) FROM public.user_marriages m 
                 WHERE m.guild_id = $2 AND m.status = 'active' 
                 AND (m.partner_a_id = $1 OR m.partner_b_id = $1) LIMIT 1) as marriage
            FROM public.users u
            LEFT JOIN public.user_economy e ON e.user_id = u.user_id AND e.guild_id = u.guild_id
            LEFT JOIN public.user_profile p ON p.user_id = u.user_id AND p.guild_id = u.guild_id
            LEFT JOIN public.user_analytics a ON a.user_id = u.user_id AND a.guild_id = u.guild_id
            WHERE u.user_id = $1 AND u.guild_id = $2
            LIMIT 1;
        """

        row = await self._neon.fetchrow(select_query, str(user_id), str(guild_id))
        if not row:
            ensure_query = """
                INSERT INTO public.users (user_id, guild_id) VALUES ($1, $2) ON CONFLICT (user_id, guild_id) DO NOTHING;
                INSERT INTO public.user_economy (user_id, guild_id) VALUES ($1, $2) ON CONFLICT (user_id, guild_id) DO NOTHING;
                INSERT INTO public.user_profile (user_id, guild_id) VALUES ($1, $2) ON CONFLICT (user_id, guild_id) DO NOTHING;
                INSERT INTO public.user_analytics (guild_id, user_id) VALUES ($2, $1) ON CONFLICT (guild_id, user_id) DO NOTHING;
            """
            await self._neon.execute(ensure_query, str(user_id), str(guild_id))
            row = await self._neon.fetchrow(select_query, str(user_id), str(guild_id))

        default_bundle = {
            "core": {"user_id": str(user_id), "guild_id": str(guild_id)},
            "economy": {
                "user_id": str(user_id),
                "guild_id": str(guild_id),
                "balance": 0,
                "deposit": 0,
                "spousal_balance": 0,
                "spousal_enabled": False,
                "cooldowns": {},
            },
            "profile": {
                "user_id": str(user_id),
                "guild_id": str(guild_id),
                "level": 1,
                "experience": 0,
                "reputation": 0,
            },
            "analytics": {
                "user_id": str(user_id),
                "guild_id": str(guild_id),
                "messages_total": 0,
                "messages_deleted": 0,
                "voice_seconds": 0,
                "message_channels": {},
                "voice_channels": {},
            },
            "marriage": None,
        }

        if not row:
            bundle = default_bundle
        else:
            bundle = {
                "core": self._ensure_dict(row["core"]) or default_bundle["core"],
                "economy": self._ensure_dict(row["economy"]) or default_bundle["economy"],
                "profile": self._ensure_dict(row["profile"]) or default_bundle["profile"],
                "analytics": self._ensure_dict(row["analytics"]) or default_bundle["analytics"],
                "marriage": self._ensure_dict(row["marriage"]) if row["marriage"] else None,
            }

        async with self._cache_lock:
            self._user_cache[key] = (bundle, time.time())
        return bundle

    async def ensure_record(self, table: str, **params: Any) -> dict[str, Any]:
        strategies = {
            "users": {
                "conflict": "user_id,guild_id",
                "lookup": ("user_id", "guild_id"),
            },
            "user_economy": {
                "conflict": "user_id,guild_id",
                "lookup": ("user_id", "guild_id"),
            },
            "user_profile": {
                "conflict": "user_id,guild_id",
                "lookup": ("user_id", "guild_id"),
            },
            "user_analytics": {
                "conflict": "guild_id,user_id",
                "lookup": ("guild_id", "user_id"),
            },
            "user_quests": {
                "conflict": "user_id,guild_id,quest_key",
                "lookup": ("user_id", "guild_id", "quest_key"),
            },
            "user_inventory": {
                "lookup": ("user_id", "guild_id", "item_type", "item_key"),
            },
            "user_marriages": {
                "lookup": ("id",),
            },
            "user_achievements": {
                "conflict": "guild_id,user_id,achievement_id",
                "lookup": ("guild_id", "user_id", "achievement_id"),
            },
            "user_rudiments": {
                "lookup": ("id",),
            },
            "user_marriage_children": {
                "lookup": ("marriage_id", "user_id"),
            },
            "settings": {
                "conflict": "key",
                "lookup": ("key",),
            },
            "temprooms": {
                "conflict": "channel_id",
                "lookup": ("channel_id",),
            },
            "partnership": {
                "conflict": "server_id",
                "lookup": ("server_id",),
            },
            "partnermanager": {
                "conflict": "id",
                "lookup": ("id",),
            },
            "giveaway_participants": {
                "conflict": "giveaway_id,user_id",
                "lookup": ("giveaway_id", "user_id"),
            },
        }

        strategy = strategies.get(table, {})
        lookup_keys = strategy.get("lookup") or tuple(params.keys())
        lookup_params = {key: params[key] for key in lookup_keys if key in params}

        if lookup_params:
            existing = await self.get_row(table, **lookup_params)
            if existing:
                return existing

        on_conflict = strategy.get("conflict")
        res = await self.upsert(table, params, on_conflict=on_conflict)
        return res[0] if res else params

    async def invalidate_user_cache(self, user_id: str, guild_id: str) -> None:
        async with self._cache_lock:
            self._user_cache.pop(f"{user_id}:{guild_id}", None)

    async def update_user_cache(self, user_id: str, guild_id: str, sub_key: str, values: dict[str, Any]) -> None:
        key = f"{user_id}:{guild_id}"
        async with self._cache_lock:
            if key in self._user_cache:
                bundle, timestamp = self._user_cache[key]
                if sub_key in bundle:
                    bundle[sub_key].update(values)
                self._user_cache[key] = (bundle, timestamp)

    async def setup_tables(self) -> None:
        await self._neon.execute("""
            CREATE TABLE IF NOT EXISTS public.custom_messages (
                guild_id  TEXT NOT NULL,
                module    TEXT NOT NULL,
                key       TEXT NOT NULL,
                value     JSONB NOT NULL DEFAULT '{}'::jsonb,
                updated_at TIMESTAMPTZ DEFAULT now(),
                PRIMARY KEY (guild_id, module, key)
            )
        """)
        await self._neon.execute("""
            CREATE TABLE IF NOT EXISTS public.premium_guilds (
                guild_id   TEXT PRIMARY KEY,
                expires_at TIMESTAMPTZ NOT NULL,
                created_at TIMESTAMPTZ DEFAULT now()
            )
        """)
        logger.info("Database tables verified (custom_messages, premium_guilds)")

    async def insert_transaction(
        self,
        user_id,
        guild_id,
        event,
        amount,
        balance_after,
        *,
        related_user_id=None,
        metadata=None,
    ) -> None:
        await self._neon.execute(
            "INSERT INTO public.user_transactions "
            "(user_id, guild_id, event, amount, balance_after, related_user_id, metadata) "
            "VALUES ($1, $2, $3, $4, $5, $6, $7)",
            str(user_id), str(guild_id), event, amount, balance_after,
            str(related_user_id) if related_user_id else None,
            json.dumps(metadata) if metadata else "{}",
        )

database = Database()
