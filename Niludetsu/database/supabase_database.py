import asyncio, json, os, time
from dotenv import load_dotenv
from Niludetsu.database.ensure_registry import EnsureRegistry
from Niludetsu.tools.Time import TimeService
from supabase import AsyncClient, acreate_client, Client, create_client
from typing import Any, Dict, List, Optional, Union

_time = TimeService()

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Sync client created at import time (needed for Leaderboard direct access etc.)
_sync_client: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

class SupabaseDatabase:
    def __init__(self):
        self.client = _sync_client
        self._async_client: Optional[AsyncClient] = None
        self._async_lock = asyncio.Lock()
        self.bot = None
        self._user_cache: Dict[str, Any] = {}
        self._cache_ttl = 300
        self._cache_lock = asyncio.Lock()
        self.ensure_registry = EnsureRegistry()

        self.ensure_registry.register(
            "users",
            keys_builder=lambda user_id, guild_id, **_: {
                "user_id": str(user_id),
                "guild_id": str(guild_id),
            },
            defaults_builder=lambda **_: {},
        )
        self.ensure_registry.register(
            "user_reminders",
            keys_builder=lambda user_id, guild_id, **_: {
                "user_id": str(user_id),
                "guild_id": str(guild_id),
            },
            defaults_builder=lambda **_: {
                "channel_id": None,
                "message": "",
                "created_at": _time.now().to_iso8601_string(),
                "remind_at": _time.now().to_iso8601_string(),
                "completed": False,
            },
        )
        self.ensure_registry.register(
            "giveaways",
            keys_builder=lambda giveaway_id=None, **payload: {"giveaway_id": giveaway_id} if giveaway_id else payload,
            defaults_builder=lambda **_: {},
        )
        self.ensure_registry.register(
            "giveaway_participants",
            keys_builder=lambda giveaway_id, user_id, **_: {
                "giveaway_id": giveaway_id,
                "user_id": str(user_id),
            },
            defaults_builder=lambda **_: {
                "joined_at": _time.now().to_iso8601_string(),
                "no_rejoin": False,
            },
        )
        self.ensure_registry.register(
            "user_economy",
            keys_builder=lambda user_id, guild_id, **_: {
                "user_id": str(user_id),
                "guild_id": str(guild_id),
            },
            defaults_builder=lambda **_: {
                "balance": 0,
                "deposit": 0,
                "spousal_balance": 0,
                "spousal_enabled": False,
                "last_daily": None,
                "last_work": None,
                "last_rob": None,
                "cooldowns": {},
            },
        )
        self.ensure_registry.register(
            "user_inventory",
            keys_builder=lambda user_id, guild_id, item_key, **_: {
                "user_id": str(user_id),
                "guild_id": str(guild_id),
                "item_key": str(item_key),
            },
            defaults_builder=lambda item_type="misc", meta=None, price_paid=0, **_: {
                "item_type": item_type,
                "meta": meta or {},
                "price_paid": price_paid,
                "acquired_at": _time.now().to_iso8601_string(),
            },
        )
        self.ensure_registry.register(
            "user_marriages",
            keys_builder=lambda guild_id, partner_a_id, partner_b_id, **_: {
                "guild_id": str(guild_id),
                "partner_a_id": str(partner_a_id),
                "partner_b_id": str(partner_b_id),
            },
            defaults_builder=lambda metadata=None, **_: {
                "status": "active",
                "metadata": metadata or {},
                "married_at": _time.now().to_iso8601_string(),
            },
        )
        self.ensure_registry.register(
            "user_marriage_children",
            keys_builder=lambda marriage_id, user_id, **_: {
                "marriage_id": marriage_id,
                "user_id": str(user_id),
            },
            defaults_builder=lambda **_: {
                "adopted_at": _time.now().to_iso8601_string(),
            },
        )
        self.ensure_registry.register(
            "user_achievements",
            keys_builder=lambda guild_id, user_id, achievement_id, **_: {
                "guild_id": str(guild_id),
                "user_id": str(user_id),
                "achievement_id": str(achievement_id),
            },
            defaults_builder=lambda metadata=None, **_: {
                "unlocked_at": _time.now().to_iso8601_string(),
                "reward_claimed": True,
                "metadata": metadata or {},
            },
        )
        self.ensure_registry.register(
            "user_profile",
            keys_builder=lambda user_id, guild_id, **_: {
                "user_id": str(user_id),
                "guild_id": str(guild_id),
            },
            defaults_builder=lambda **_: {
                "level": 1,
                "experience": 0,
                "reputation": 0,
                "updated_at": _time.now().to_iso8601_string(),
            },
        )
        self.ensure_registry.register(
            "user_analytics",
            keys_builder=lambda user_id, guild_id, **_: {
                "user_id": str(user_id),
                "guild_id": str(guild_id),
            },
            defaults_builder=lambda **_: {
                "messages_total": 0,
                "messages_deleted": 0,
                "voice_seconds": 0,
                "message_channels": {},
                "voice_channels": {},
                "last_voice_join": None,
                "last_updated": _time.now().to_iso8601_string(),
            },
        )
        self.ensure_registry.register(
            "temprooms",
            keys_builder=lambda channel_id, **_: {
                "channel_id": str(channel_id),
            },
            defaults_builder=lambda guild_id=None, owner_id=None, name=None, **_: {
                "guild_id": str(guild_id) if guild_id is not None else "0",
                "owner_id": str(owner_id) if owner_id is not None else "0",
                "name": name or "🔊 {name}",
                "user_limit": 0,
                "is_private": False,
                "locked": False,
                "access_mode": "open",
                "access_list": [],
                "remember_settings": False,
                "active": True,
                "created_at": _time.now().to_iso8601_string(),
                "updated_at": _time.now().to_iso8601_string(),
            },
        )
        self.ensure_registry.register(
            "user_quests",
            keys_builder=lambda user_id, guild_id, quest_key, **_: {
                "user_id": str(user_id),
                "guild_id": str(guild_id),
                "quest_key": str(quest_key),
            },
            defaults_builder=lambda resets_at=None, **_: {
                "progress": 0,
                "completed": False,
                "reward_claimed": False,
                "started_at": _time.now().to_iso8601_string(),
                "completed_at": None,
                "resets_at": resets_at or _time.now().add(days=1).to_iso8601_string(),
            },
        )

    # Async client (lazy init)
    async def _aclient(self) -> AsyncClient:
        if self._async_client is not None:
            return self._async_client
        async with self._async_lock:
            if self._async_client is None:
                self._async_client = await acreate_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
            return self._async_client

    def _table(self, name: str):
        return self.client.table(name)

    async def _atable(self, name: str):
        c = await self._aclient()
        return c.table(name)

    # Cache
    def _cache_key(self, user_id: str, guild_id: str) -> str:
        return f"{user_id}:{guild_id}"

    async def _get_cached_user(self, user_id: str, guild_id: str) -> Optional[Dict[str, Any]]:
        key = self._cache_key(user_id, guild_id)
        async with self._cache_lock:
            cached = self._user_cache.get(key)
            if not cached:
                return None
            data, ts = cached
            if time.time() - ts < self._cache_ttl:
                return json.loads(json.dumps(data))
            self._user_cache.pop(key, None)
            return None

    async def _cache_user(self, user_id: str, guild_id: str, data: Dict[str, Any]) -> None:
        key = self._cache_key(user_id, guild_id)
        async with self._cache_lock:
            self._user_cache[key] = (json.loads(json.dumps(data)), time.time())
            if len(self._user_cache) > 1000:
                now = time.time()
                stale = [k for k, (_, ts) in self._user_cache.items() if now - ts >= self._cache_ttl]
                for k in stale:
                    self._user_cache.pop(k, None)

    async def invalidate_user_cache(self, user_id: str, guild_id: str) -> None:
        key = self._cache_key(user_id, guild_id)
        async with self._cache_lock:
            self._user_cache.pop(key, None)

    async def _merge_json_fields(
        self,
        table: str,
        where: Dict[str, Any],
        payload: Dict[str, Any],
        json_fields: Optional[List[str]],
    ) -> Dict[str, Any]:
        if not json_fields:
            return payload

        current = await self.get_row(table, **where)
        if not current:
            return payload

        merged = payload.copy()
        for field in json_fields:
            if field in payload and field in current:
                current_value = current[field] or {}
                new_value = payload[field] or {}
                if isinstance(current_value, dict) and isinstance(new_value, dict):
                    current_value.update(new_value)
                    merged[field] = current_value
        return merged

    # CRUD (true async via AsyncClient)
    async def get_row(self, table: str, **conditions) -> Optional[Dict[str, Any]]:
        t = await self._atable(table)
        query = t.select("*")
        for key, value in conditions.items():
            query = query.eq(key, value)
        try:
            response = await query.single().execute()
            return response.data
        except Exception:
            return None

    async def get_rows(self, table: str, **conditions) -> List[Dict[str, Any]]:
        t = await self._atable(table)
        query = t.select("*")
        for key, value in conditions.items():
            query = query.eq(key, value)
        response = await query.execute()
        return response.data or []

    async def insert(self, table: str, values: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        t = await self._atable(table)
        response = await t.insert(values).execute()
        return response.data[0] if response.data else None

    async def update_record(
        self,
        table: str,
        where: Dict[str, Any],
        values: Dict[str, Any],
        *,
        json_fields: Optional[List[str]] = None,
        ensure_if_missing: bool = False,
        ensure_params: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        payload = await self._merge_json_fields(table, where, values.copy(), json_fields)

        t = await self._atable(table)
        query = t.update(payload)
        for key, value in where.items():
            query = query.eq(key, value)

        response = await query.execute()
        rows = response.data or []

        if {"user_id", "guild_id"} <= set(where.keys()):
            await self.invalidate_user_cache(str(where["user_id"]), str(where["guild_id"]))

        if rows:
            return rows[0]

        if ensure_if_missing:
            params = ensure_params or where
            return await self.ensure_record(table, **params)

        return None

    async def delete(self, table: str, **conditions) -> int:
        t = await self._atable(table)
        query = t.delete()
        for key, value in conditions.items():
            query = query.eq(key, value)
        response = await query.execute()
        return len(response.data or [])

    async def where(
        self,
        table: str,
        *,
        columns: Optional[List[str]] = None,
        filters: Optional[List[Dict[str, Any]]] = None,
        order: Optional[List[Dict[str, Any]]] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        t = await self._atable(table)
        query = t.select(", ".join(columns) if columns else "*")
        if filters:
            for flt in filters:
                op = flt.get("op", "eq")
                column = flt["column"]
                value = flt["value"]

                if op == "is":
                    query = query.is_(column, value)
                else:
                    query = getattr(query, op)(column, value)
        if order:
            for rule in order:
                query = query.order(
                    rule["column"],
                    desc=not rule.get("ascending", True),
                    nullsfirst=rule.get("nulls_first", False),
                )
        if limit:
            query = query.limit(limit)
        response = await query.execute()
        return response.data or []

    async def upsert(
        self,
        table: str,
        payload: Union[Dict[str, Any], List[Dict[str, Any]]],
        *,
        on_conflict: Optional[str] = None,
        returning: Optional[str] = "representation",
    ):
        t = await self._atable(table)

        kwargs: Dict[str, Any] = {}
        if on_conflict:
            kwargs["on_conflict"] = on_conflict
        if returning:
            kwargs["returning"] = returning

        result = t.upsert(payload, **kwargs)

        if hasattr(result, "execute"):
            result = await result.execute()

        return getattr(result, "data", result)

    # Ensure
    async def ensure_record(self, table: str, **params) -> Dict[str, Any]:
        keys, defaults = self.ensure_registry.resolve(table, **params)
        existing = await self.get_row(table, **keys)
        if existing:
            return existing

        payload = {**keys, **defaults}
        created = await self.insert(table, payload)
        return created or payload

    async def ensure_user(self, user_id: str, guild_id: str) -> Dict[str, Any]:
        cached = await self._get_cached_user(user_id, guild_id)
        if cached:
            return cached

        core, economy, profile, analytics, reminders = await asyncio.gather(
            self.ensure_record("users", user_id=user_id, guild_id=guild_id),
            self.ensure_record("user_economy", user_id=user_id, guild_id=guild_id),
            self.ensure_record("user_profile", user_id=user_id, guild_id=guild_id),
            self.ensure_record("user_analytics", user_id=user_id, guild_id=guild_id),
            self.get_rows(
                "user_reminders",
                user_id=str(user_id),
                guild_id=str(guild_id),
                completed=False,
            ),
        )

        bundle = {
            "core": core,
            "economy": economy,
            "profile": profile,
            "analytics": analytics,
            "reminders": reminders,
        }

        await self._cache_user(user_id, guild_id, bundle)
        return bundle

    async def get_user(self, user_id: str, guild_id: str) -> Dict[str, Any]:
        return await self.ensure_user(user_id, guild_id)

    # Настройки / общее
    async def get_setting(self, category: str, key: str, default=None, guild_id: str = "0"):
        t = await self._atable("settings")
        try:
            response = await (
                t.select("value")
                .eq("guild_id", guild_id)
                .eq("category", category)
                .eq("key", key)
                .single()
                .execute()
            )
        except Exception:
            return default
        if not response.data:
            return default
        value = response.data["value"]
        if isinstance(value, str) and (value.startswith("{") or value.startswith("[")):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value

    async def is_bot(self, user_id: str) -> bool:
        if not self.bot:
            return False
        try:
            user = await self.bot.fetch_user(int(user_id))
            return user.bot
        except Exception:
            return False

    async def close(self):
        async with self._cache_lock:
            self._user_cache.clear()

    def set_bot(self, bot):
        self.bot = bot

    # Утилиты
    async def update_economy(
        self,
        user_id: str,
        guild_id: str,
        values: Dict[str, Any],
        *,
        json_fields: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        if json_fields is None:
            json_fields = ["cooldowns"]
        where = {"user_id": str(user_id), "guild_id": str(guild_id)}
        return await self.update_record(
            "user_economy",
            where,
            values,
            json_fields=json_fields,
            ensure_if_missing=True,
            ensure_params=where,
        )

    async def fetch_inventory_items(self, user_id: str, guild_id: str) -> List[Dict[str, Any]]:
        return await self.get_rows(
            "user_inventory",
            user_id=str(user_id),
            guild_id=str(guild_id),
        )

    async def ensure_inventory_item(
        self,
        user_id: str,
        guild_id: str,
        item_key: str,
        *,
        item_type: str = "misc",
        meta: Optional[Dict[str, Any]] = None,
        price_paid: int = 0,
    ) -> Dict[str, Any]:
        return await self.ensure_record(
            "user_inventory",
            user_id=user_id,
            guild_id=guild_id,
            item_key=item_key,
            item_type=item_type,
            meta=meta,
            price_paid=price_paid,
        )

    async def delete_inventory_item(self, user_id: str, guild_id: str, item_key: str) -> int:
        return await self.delete(
            "user_inventory",
            user_id=str(user_id),
            guild_id=str(guild_id),
            item_key=str(item_key),
        )

    async def fetch_owned_role(self, guild_id: str, role_id: str) -> Optional[Dict[str, Any]]:
        return await self.get_row(
            "roles",
            guild_id=str(guild_id),
            role_id=str(role_id),
        )

    async def get_active_marriage(self, guild_id: str, user_id: str) -> Optional[Dict[str, Any]]:
            rows = await self.where(
                "user_marriages",
                filters=[
                    {"column": "guild_id", "value": str(guild_id)},
                    {"column": "status", "value": "active"},
                    {"column": "partner_a_id", "value": str(user_id), "op": "eq"},
                ],
            )
            if rows:
                return rows[0]
            rows = await self.where(
                "user_marriages",
                filters=[
                    {"column": "guild_id", "value": str(guild_id)},
                    {"column": "status", "value": "active"},
                    {"column": "partner_b_id", "value": str(user_id), "op": "eq"},
                ],
            )
            return rows[0] if rows else None

    async def ensure_marriage_record(
        self,
        guild_id: str,
        partner_a_id: str,
        partner_b_id: str,
        *,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return await self.ensure_record(
            "user_marriages",
            guild_id=guild_id,
            partner_a_id=partner_a_id,
            partner_b_id=partner_b_id,
            metadata=metadata,
        )

    async def close_marriage(self, marriage_id: str, *, status: str = "divorced") -> None:
            await self.update_record(
                "user_marriages",
                {"id": marriage_id},
                {
                    "status": status,
                    "metadata": {"closed_at": _time.now().to_iso8601_string()},
                },
                json_fields=["metadata"],
            )

    async def get_marriage_partner(self, marriage: Dict[str, Any], user_id: str) -> str:
        a = marriage["partner_a_id"]
        b = marriage["partner_b_id"]
        return b if str(a) == str(user_id) else a

    async def fetch_children(self, marriage_id: str) -> List[Dict[str, Any]]:
        return await self.get_rows("user_marriage_children", marriage_id=marriage_id)

    async def add_child(self, marriage_id: str, user_id: str) -> Dict[str, Any]:
        return await self.ensure_record(
            "user_marriage_children",
            marriage_id=marriage_id,
            user_id=user_id,
        )

    async def remove_child(self, marriage_id: str, user_id: str) -> None:
        await self.delete(
            "user_marriage_children",
            marriage_id=marriage_id,
            user_id=str(user_id),
        )

    async def list_achievements(self, guild_id: str, user_id: str) -> List[Dict[str, Any]]:
        return await self.get_rows(
            "user_achievements",
            guild_id=str(guild_id),
            user_id=str(user_id),
        )

    async def ensure_achievement(
        self,
        guild_id: str,
        user_id: str,
        achievement_id: str,
        *,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return await self.ensure_record(
            "user_achievements",
            guild_id=guild_id,
            user_id=user_id,
            achievement_id=achievement_id,
            metadata=metadata,
        )

    async def remove_achievement(self, guild_id: str, user_id: str, achievement_id: str) -> None:
        await self.delete(
            "user_achievements",
            guild_id=str(guild_id),
            user_id=str(user_id),
            achievement_id=str(achievement_id),
        )

    # Транзакции
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
    ) -> Optional[Dict[str, Any]]:
        return await self.insert("user_transactions", {
            "user_id": str(user_id),
            "guild_id": str(guild_id),
            "event": event,
            "amount": amount,
            "balance_after": balance_after,
            "related_user_id": str(related_user_id) if related_user_id else None,
            "metadata": metadata or {},
        })

    async def get_transactions(
        self,
        user_id,
        guild_id,
        *,
        limit: int = 10,
        offset: int = 0,
        events: Optional[List[str]] = None,
    ):
        t = await self._atable("user_transactions")
        query = (
            t.select("*", count="exact")
            .eq("user_id", str(user_id))
            .eq("guild_id", str(guild_id))
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
        )
        if events:
            query = query.in_("event", events)
        response = await query.execute()
        return response.data or [], response.count or 0

database = SupabaseDatabase()
