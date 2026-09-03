import asyncio, time
from collections import defaultdict
from dataclasses import dataclass
from Niludetsu import TimeService
from Niludetsu.locale import _
from Niludetsu.database import database
from typing import Dict, List, Optional, Tuple, Any

_time = TimeService()


@dataclass
class PartnershipProcessResult:
    success: bool = False
    is_new: bool = False
    points: int = 0
    message: str = ""
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "is_new": self.is_new,
            "points": self.points,
            "message": self.message,
            "error": self.error
        }

class InviteCache:

    def __init__(self, ttl: int = 3600):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = ttl

    def get(self, invite_code: str) -> Optional[Dict[str, Any]]:
        if invite_code not in self.cache:
            return None

        entry = self.cache[invite_code]
        if time.time() - entry["timestamp"] > self.ttl:
            del self.cache[invite_code]
            return None

        return entry["data"]

    def set(self, invite_code: str, data: Dict[str, Any]):
        self.cache[invite_code] = {
            "data": data,
            "timestamp": time.time()
        }

    def invalidate(self, invite_code: str):
        self.cache.pop(invite_code, None)

    def clear(self):
        self.cache.clear()

class StatsCache:

    def __init__(self, ttl: int = 300):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self.ttl = ttl

    async def get(self, user_id: str) -> Optional[Dict[str, Any]]:
        if user_id not in self.cache:
            return None

        entry = self.cache[user_id]
        if time.time() - entry["timestamp"] > self.ttl:
            del self.cache[user_id]
            return None

        return entry["data"]

    async def set(self, user_id: str, data: Dict[str, Any]):
        async with self.locks[user_id]:
            self.cache[user_id] = {
                "data": data,
                "timestamp": time.time()
            }

    async def invalidate(self, user_id: str):
        self.cache.pop(user_id, None)

    async def clear(self):
        self.cache.clear()

class ProcessingQueue:

    def __init__(self):
        self.server_locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self.user_locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    async def acquire_server_lock(self, server_id: str) -> asyncio.Lock:
        return self.server_locks[server_id]

    async def acquire_user_lock(self, user_id: str) -> asyncio.Lock:
        return self.user_locks[user_id]

class PartnershipScoring:

    POINTS_NEW = 2
    POINTS_RENEWAL_12H = 1
    POINTS_RENEWAL_BEFORE = 0
    RENEWAL_THRESHOLD = 43200

    def __init__(self, main_server_id: int):
        self.main_server_id = str(main_server_id)

    def calculate_new_points(self) -> int:
        return self.POINTS_NEW

    def calculate_renewal_points(self, last_renewal_timestamp: int) -> Tuple[int, str]:
        now = int(time.time())
        time_since = now - last_renewal_timestamp

        if time_since >= self.RENEWAL_THRESHOLD:
            return (
                self.POINTS_RENEWAL_12H,
                f"✅ Начислен **{self.POINTS_RENEWAL_12H}** балл за обновление (прошло >12ч)"
            )

        hours = time_since / 3600
        return (
            self.POINTS_RENEWAL_BEFORE,
            f"⏳ Обновление без баллов (прошло {hours:.1f}ч из 12ч)"
        )

    def check_self_invite(self, server_id: str) -> Tuple[bool, str]:
        if server_id == self.main_server_id:
            return (
                True,
                "😏 Партнёрство с самими собой? Найдите другой сервер!"
            )
        return (False, "")

class BlacklistManager:

    def __init__(self, bot, db):
        self.bot = bot
        self.db = database

    async def is_blacklisted(self, server_id: str) -> bool:
        rows = await self.db.where(
            "partnership",
            filters=[
                {"column": "server_id", "value": server_id},
                {"column": "is_blacklisted", "value": True}
            ],
            limit=1
        )
        return len(rows) > 0

    async def add(self, server_id: str, server_name: str = None) -> bool:
        if not server_name:
            server_name = await self._get_server_name(server_id)

        existing = await self.db.where(
            "partnership",
            filters=[{"column": "server_id", "value": server_id}],
            limit=1
        )

        if existing:
            await self.db.update_record(
                "partnership",
                {"server_id": server_id},
                {"is_blacklisted": True, "server_name": server_name}
            )
        else:
            now_dt = _time.now()
            await self.db.insert("partnership", {
                "server_id": server_id,
                "server_name": server_name,
                "is_blacklisted": True,
                "invite_code": "",
                "manager_id": "0",
                "created_at": now_dt.format("YYYY-MM-DDTHH:mm:ssZ"),
                "renewed_count": 0,
                "last_renewal": now_dt.format("YYYY-MM-DDTHH:mm:ssZ")
            })
        return True

    async def remove(self, server_id: str) -> bool:
        rows = await self.db.where(
            "partnership",
            filters=[{"column": "server_id", "value": server_id}],
            limit=1
        )

        if rows:
            await self.db.update_record(
                "partnership",
                {"server_id": server_id},
                {"is_blacklisted": False}
            )
            return True
        return False

    async def get_all(self) -> List[Dict[str, str]]:
        rows = await self.db.where(
            "partnership",
            filters=[{"column": "is_blacklisted", "value": True}]
        )

        blacklisted = []
        for row in rows:
            current_name = await self._get_server_name(row["server_id"])
            if current_name and current_name != row["server_name"]:
                await self.db.update_record(
                    "partnership",
                    {"server_id": row["server_id"]},
                    {"server_name": current_name}
                )

            blacklisted.append({
                "server_id": row["server_id"],
                "server_name": current_name or row["server_name"] or "Неизвестный сервер"
            })

        return blacklisted

    async def check_message(self, server_id: str, server_name: str = None) -> Optional[Dict[str, str]]:
        if await self.is_blacklisted(server_id):
            t = _(bot=self.bot)
            if not server_name:
                server_name = await self._get_server_name(server_id) or "Неизвестный сервер"

            return {
                "title": "❌ Сервер в чёрном списке",
                "description": f"Сервер **{server_name}** находится в чёрном списке."
            }
        return None

    async def _get_server_name(self, server_id: str) -> Optional[str]:
        try:
            guild = self.bot.get_guild(int(server_id))
            return guild.name if guild else None
        except:
            return None

class PartnershipManager:

    def __init__(self, bot, main_server_id: int):
        self.bot = bot
        self.db = database
        self.main_server_id = str(main_server_id)

        self.scoring = PartnershipScoring(main_server_id)
        self.blacklist = BlacklistManager(bot, self.db)
        self.invite_cache = InviteCache(ttl=3600)
        self.stats_cache = StatsCache(ttl=300)
        self.processing_queue = ProcessingQueue()
        self.queue = self.processing_queue

    async def get_invite_info(self, invite_code: str) -> Optional[Dict[str, Any]]:
        partnership = await self._get_partnership_by_invite_code(invite_code)
        if partnership:
            info = self._build_db_invite_info(partnership, invite_code)
            self.invite_cache.set(invite_code, info)
            return info

        cached = self.invite_cache.get(invite_code)
        if cached:
            return cached

        try:
            invite = await self.bot.fetch_invite(invite_code)
            if not invite or not invite.guild:
                return None

            info = {
                "server_id": str(invite.guild.id),
                "server_name": invite.guild.name,
                "member_count": invite.approximate_member_count,
                "invite_code": invite.code,
                "from_db": False
            }

            self.invite_cache.set(invite_code, info)
            return info

        except Exception as e:
            print(f"[Partnership] Ошибка получения инвайта: {e}")
            return None

    async def process_partnership(self, server_id: str, server_name: str, 
                                 invite_code: str, manager_id: str) -> Dict[str, Any]:
        validation_error = await self._validate_partnership(server_id, server_name)
        if validation_error:
            return validation_error.to_dict()

        existing = await self._get_partnership_by_server_id(server_id)
        if existing:
            result = await self._process_existing_partnership(
                existing,
                server_id,
                server_name,
                invite_code,
                manager_id
            )
        else:
            result = await self._process_new_partnership(
                server_id,
                server_name,
                invite_code,
                manager_id
            )

        await self.stats_cache.invalidate(manager_id)
        return result.to_dict()

    async def _update_manager_stats(self, manager_id: str, new_points: int = 0, 
                                   renewal_points: int = 0):
        await self._ensure_manager(manager_id)

        points_delta = new_points + renewal_points
        sets = []
        params = [str(manager_id)]
 
        if points_delta > 0:
            sets.append(f"points = points + ${len(params)+1}")
            params.append(points_delta)

        if new_points > 0:
            sets.append("new_partnerships = new_partnerships + 1")

        if renewal_points > 0:
            sets.append("renewed_partnerships = renewed_partnerships + 1")

        if not sets:
            return

        query = f"UPDATE public.partnermanager SET {', '.join(sets)} WHERE id = $1 RETURNING *"
        await self.db._neon.fetchrow(query, *params)

    async def _ensure_manager(self, manager_id: str):
        if not await self._get_manager_row(manager_id):
            await self.db.insert("partnermanager", {
                "id": manager_id,
                "points": 0,
                "new_partnerships": 0,
                "renewed_partnerships": 0,
                "is_active": True
            })

    async def get_manager_stats(self, manager_id: str, use_cache: bool = True) -> Dict[str, Any]:
        if use_cache:
            cached = await self.stats_cache.get(manager_id)
            if cached:
                return cached

        manager = await self._get_or_create_manager(manager_id)
        partnerships = await self.db.where(
            "partnership",
            filters=[{"column": "manager_id", "value": manager_id}]
        )
        stats = self._build_manager_stats(manager, partnerships)

        if use_cache:
            await self.stats_cache.set(manager_id, stats)

        return stats

    async def get_user_points(self, user_id: str) -> int:
        manager = await self._get_or_create_manager(user_id)
        return manager["points"] if manager else 0

    async def update_pm_stats(self, user_id: str, points: int = 0):
        manager = await self._get_or_create_manager(user_id)
        if manager:
            new_points = manager["points"] + points
            await self.db.update_record(
                "partnermanager",
                {"id": user_id},
                {"points": new_points}
            )
            await self.stats_cache.invalidate(user_id)

    async def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        capped_limit = min(max(limit or 10, 1), 50)

        rows = await self.db.where(
            "partnermanager",
            order=[{"column": "points", "ascending": False}],
            limit=capped_limit
        )

        return [{
            "user_id": row["id"],
            "points": row["points"],
            "new_partnerships": row["new_partnerships"],
            "renewed_partnerships": row["renewed_partnerships"],
            "partnerships_count": row["new_partnerships"]
        } for row in rows]

    async def _validate_partnership(
        self,
        server_id: str,
        server_name: str
    ) -> Optional[PartnershipProcessResult]:
        is_self, message = self.scoring.check_self_invite(server_id)
        if is_self:
            return PartnershipProcessResult(
                error="self_invite",
                message=message
            )

        blacklist_check = await self.blacklist.check_message(server_id, server_name)
        if blacklist_check:
            return PartnershipProcessResult(
                error="blacklisted",
                message=blacklist_check["description"]
            )

        return None

    async def _process_existing_partnership(
        self,
        existing: Dict[str, Any],
        server_id: str,
        server_name: str,
        invite_code: str,
        manager_id: str
    ) -> PartnershipProcessResult:
        points, message = self._calculate_renewal(existing)
        await self._update_existing_partnership(
            existing,
            server_id,
            server_name,
            invite_code,
            manager_id,
            points
        )
        self.invite_cache.invalidate(invite_code)

        if points > 0:
            await self._update_manager_stats(manager_id, renewal_points=points)

        return PartnershipProcessResult(
            success=True,
            is_new=False,
            points=points,
            message=message
        )

    async def _process_new_partnership(
        self,
        server_id: str,
        server_name: str,
        invite_code: str,
        manager_id: str
    ) -> PartnershipProcessResult:
        points = self.scoring.calculate_new_points()
        await self._create_partnership(server_id, server_name, invite_code, manager_id)
        await self._update_manager_stats(manager_id, new_points=points)
        return PartnershipProcessResult(
            success=True,
            is_new=True,
            points=points,
            message=f"✅ Начислено **{points}** балла за новое партнёрство!"
        )

    def _calculate_renewal(self, existing: Dict[str, Any]) -> Tuple[int, str]:
        last_renewal_ts = int(_time.ensure_datetime(existing["last_renewal"]).timestamp())
        return self.scoring.calculate_renewal_points(last_renewal_ts)

    async def _update_existing_partnership(
        self,
        existing: Dict[str, Any],
        server_id: str,
        server_name: str,
        invite_code: str,
        manager_id: str,
        points: int
    ):
        now_str = self._now_formatted()
        await self.db.update_record(
            "partnership",
            {"server_id": server_id},
            {
                "server_name": server_name,
                "invite_code": invite_code,
                "manager_id": manager_id,
                "last_renewal": now_str,
                "renewed_count": existing["renewed_count"] + (1 if points > 0 else 0)
            }
        )

    async def _create_partnership(
        self,
        server_id: str,
        server_name: str,
        invite_code: str,
        manager_id: str
    ):
        now_str = self._now_formatted()
        await self.db.insert("partnership", {
            "server_id": server_id,
            "server_name": server_name,
            "invite_code": invite_code,
            "manager_id": manager_id,
            "created_at": now_str,
            "renewed_count": 0,
            "last_renewal": now_str,
            "is_blacklisted": False
        })

    def _build_manager_stats(
        self,
        manager: Dict[str, Any],
        partnerships: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        servers = sorted(
            (self._build_server_stats(partnership) for partnership in partnerships),
            key=lambda server: server["last_renewal"],
            reverse=True
        )
        return {
            "points": manager["points"],
            "new_partnerships": manager["new_partnerships"],
            "renewed_partnerships": manager["renewed_partnerships"],
            "partnerships_count": len(partnerships),
            "servers": servers
        }

    def _build_server_stats(self, partnership: Dict[str, Any]) -> Dict[str, Any]:
        last_renewal_dt = _time.ensure_datetime(partnership["last_renewal"])
        return {
            "server_id": partnership["server_id"],
            "server_name": partnership["server_name"],
            "last_renewal": int(last_renewal_dt.timestamp()),
            "renewed_count": partnership["renewed_count"]
        }

    def _build_db_invite_info(
        self,
        partnership: Dict[str, Any],
        invite_code: str
    ) -> Dict[str, Any]:
        return {
            "server_id": partnership["server_id"],
            "server_name": partnership["server_name"],
            "invite_code": invite_code,
            "from_db": True
        }

    async def _get_partnership_by_server_id(self, server_id: str) -> Optional[Dict[str, Any]]:
        return await self._get_single_row(
            "partnership",
            [{"column": "server_id", "value": server_id}]
        )

    async def _get_partnership_by_invite_code(self, invite_code: str) -> Optional[Dict[str, Any]]:
        return await self._get_single_row(
            "partnership",
            [{"column": "invite_code", "value": invite_code}]
        )

    async def _get_manager_row(self, manager_id: str) -> Optional[Dict[str, Any]]:
        return await self._get_single_row(
            "partnermanager",
            [{"column": "id", "value": manager_id}]
        )

    async def _get_or_create_manager(self, manager_id: str) -> Optional[Dict[str, Any]]:
        await self._ensure_manager(manager_id)
        return await self._get_manager_row(manager_id)

    async def _get_single_row(
        self,
        table: str,
        filters: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        rows = await self.db.where(table, filters=filters, limit=1)
        return rows[0] if rows else None

    def _now_formatted(self) -> str:
        return _time.now().format("YYYY-MM-DDTHH:mm:ssZ")

async def setup(bot):
    pass
