import asyncio, time
from collections import defaultdict
from Niludetsu import TimeService
from Niludetsu.database.supabase_database import database
from typing import Dict, List, Optional, Tuple, Any

_time = TimeService()

class InviteCache:
    """Кеш инвайтов для минимизации запросов к Discord API"""

    def __init__(self, ttl: int = 3600):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = ttl

    def get(self, invite_code: str) -> Optional[Dict[str, Any]]:
        """Получает инвайт из кеша"""
        if invite_code not in self.cache:
            return None

        entry = self.cache[invite_code]
        if time.time() - entry["timestamp"] > self.ttl:
            del self.cache[invite_code]
            return None

        return entry["data"]

    def set(self, invite_code: str, data: Dict[str, Any]):
        """Сохраняет инвайт в кеш"""
        self.cache[invite_code] = {
            "data": data,
            "timestamp": time.time()
        }

    def invalidate(self, invite_code: str):
        """Удаляет инвайт из кеша"""
        self.cache.pop(invite_code, None)

    def clear(self):
        """Очищает весь кеш"""
        self.cache.clear()

class StatsCache:
    """Кеш статистики ПМов"""

    def __init__(self, ttl: int = 300):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self.ttl = ttl

    async def get(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Получает статистику из кеша"""
        if user_id not in self.cache:
            return None

        entry = self.cache[user_id]
        if time.time() - entry["timestamp"] > self.ttl:
            del self.cache[user_id]
            return None

        return entry["data"]

    async def set(self, user_id: str, data: Dict[str, Any]):
        """Сохраняет статистику в кеш"""
        async with self.locks[user_id]:
            self.cache[user_id] = {
                "data": data,
                "timestamp": time.time()
            }

    async def invalidate(self, user_id: str):
        """Удаляет статистику из кеша"""
        self.cache.pop(user_id, None)

    async def clear(self):
        """Очищает весь кеш"""
        self.cache.clear()

class ProcessingQueue:
    """Очередь обработки для предотвращения дубликатов"""

    def __init__(self):
        self.server_locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self.user_locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    async def acquire_server_lock(self, server_id: str) -> asyncio.Lock:
        """Получает блокировку для сервера"""
        return self.server_locks[server_id]

    async def acquire_user_lock(self, user_id: str) -> asyncio.Lock:
        """Получает блокировку для пользователя"""
        return self.user_locks[user_id]

class PartnershipScoring:
    """Система подсчёта баллов"""

    POINTS_NEW = 2              # За новое партнёрство
    POINTS_RENEWAL_12H = 1      # За обновление после 12 часов
    POINTS_RENEWAL_BEFORE = 0   # За обновление до 12 часов
    RENEWAL_THRESHOLD = 43200   # 12 часов в секундах

    def __init__(self, main_server_id: int):
        self.main_server_id = str(main_server_id)

    def calculate_new_points(self) -> int:
        """Баллы за новое партнёрство"""
        return self.POINTS_NEW

    def calculate_renewal_points(self, last_renewal_timestamp: int) -> Tuple[int, str]:
        """Баллы за обновление партнёрства"""
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
        """Проверка на самоинвайт"""
        if server_id == self.main_server_id:
            return (
                True,
                "😏 Партнёрство с самими собой? Найдите другой сервер!"
            )
        return (False, "")

class BlacklistManager:
    """Управление чёрным списком серверов"""

    def __init__(self, bot, db):
        self.bot = bot
        self.db = database

    async def is_blacklisted(self, server_id: str) -> bool:
        """Проверяет, в чёрном списке ли сервер"""
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
        """Добавляет сервер в чёрный список"""
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
        """Удаляет сервер из чёрного списка"""
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
        """Получает список всех серверов в чёрном списке"""
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
        """Проверяет сервер и возвращает сообщение если в чёрном списке"""
        if await self.is_blacklisted(server_id):
            if not server_name:
                server_name = await self._get_server_name(server_id) or "Неизвестный сервер"

            return {
                "title": "❌ Сервер в чёрном списке",
                "description": f"Сервер **{server_name}** находится в чёрном списке."
            }
        return None

    async def _get_server_name(self, server_id: str) -> Optional[str]:
        """Получает название сервера через Discord API"""
        try:
            guild = self.bot.get_guild(int(server_id))
            return guild.name if guild else None
        except:
            return None

class PartnershipManager:
    """Главный менеджер партнёрств"""

    def __init__(self, bot, main_server_id: int):
        self.bot = bot
        self.db = database
        self.main_server_id = str(main_server_id)

        # Подсистемы
        self.scoring = PartnershipScoring(main_server_id)
        self.blacklist = BlacklistManager(bot, self.db)
        self.invite_cache = InviteCache(ttl=3600)
        self.stats_cache = StatsCache(ttl=300)
        self.processing_queue = ProcessingQueue()
        self.queue = self.processing_queue

    async def get_invite_info(self, invite_code: str) -> Optional[Dict[str, Any]]:
        """
        Получает информацию об инвайте: БД → Кеш → Discord API
        """
        # 1️⃣ БД (самый быстрый)
        db_rows = await self.db.where(
            "partnership",
            filters=[{"column": "invite_code", "value": invite_code}],
            limit=1
        )

        if db_rows:
            p = db_rows[0]
            info = {
                "server_id": p["server_id"],
                "server_name": p["server_name"],
                "invite_code": invite_code,
                "from_db": True
            }
            self.invite_cache.set(invite_code, info)
            return info

        # 2️⃣ Кеш (быстро)
        cached = self.invite_cache.get(invite_code)
        if cached:
            return cached

        # 3️⃣ Discord API (медленно)
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
        """Обрабатывает создание/обновление партнёрства"""
        result = {
            "success": False,
            "is_new": False,
            "points": 0,
            "message": "",
            "error": None
        }

        # Проверка на самоинвайт
        is_self, msg = self.scoring.check_self_invite(server_id)
        if is_self:
            result["error"] = "self_invite"
            result["message"] = msg
            return result

        # Проверка чёрного списка
        blacklist_check = await self.blacklist.check_message(server_id, server_name)
        if blacklist_check:
            result["error"] = "blacklisted"
            result["message"] = blacklist_check["description"]
            return result

        # Проверяем существующее партнёрство
        existing_rows = await self.db.where(
            "partnership",
            filters=[{"column": "server_id", "value": server_id}],
            limit=1
        )

        existing = existing_rows[0] if existing_rows else None

        if existing:
            # ОБНОВЛЕНИЕ
            last_renewal_ts = int(_time.ensure_datetime(existing["last_renewal"]).timestamp())
            points, msg = self.scoring.calculate_renewal_points(last_renewal_ts)

            now_dt = _time.now()
            await self.db.update_record(
                "partnership",
                {"server_id": server_id},
                {
                    "server_name": server_name,
                    "invite_code": invite_code,
                    "manager_id": manager_id,
                    "last_renewal": now_dt.format("YYYY-MM-DDTHH:mm:ssZ"),
                    "renewed_count": existing["renewed_count"] + (1 if points > 0 else 0)
                }
            )

            self.invite_cache.invalidate(invite_code)

            if points > 0:
                await self._update_manager_stats(manager_id, renewal_points=points)

            result["success"] = True
            result["is_new"] = False
            result["points"] = points
            result["message"] = msg

        else:
            # НОВОЕ ПАРТНЁРСТВО
            points = self.scoring.calculate_new_points()
            now_dt = _time.now()

            await self.db.insert("partnership", {
                "server_id": server_id,
                "server_name": server_name,
                "invite_code": invite_code,
                "manager_id": manager_id,
                "created_at": now_dt.format("YYYY-MM-DDTHH:mm:ssZ"),
                "renewed_count": 0,
                "last_renewal": now_dt.format("YYYY-MM-DDTHH:mm:ssZ"),
                "is_blacklisted": False
            })

            await self._update_manager_stats(manager_id, new_points=points)

            result["success"] = True
            result["is_new"] = True
            result["points"] = points
            result["message"] = f"✅ Начислено **{points}** балла за новое партнёрство!"

        await self.stats_cache.invalidate(manager_id)
        return result

    async def _update_manager_stats(self, manager_id: str, new_points: int = 0, 
                                   renewal_points: int = 0):
        """Обновляет статистику менеджера"""
        await self._ensure_manager(manager_id)

        current_rows = await self.db.where(
            "partnermanager",
            filters=[{"column": "id", "value": manager_id}],
            limit=1
        )
        current = current_rows[0] if current_rows else None

        if not current:
            return

        update = {}

        if new_points > 0:
            update["points"] = current["points"] + new_points
            update["new_partnerships"] = current["new_partnerships"] + 1

        if renewal_points > 0:
            update["points"] = current.get("points", current["points"]) + renewal_points
            update["renewed_partnerships"] = current["renewed_partnerships"] + 1

        if update:
            await self.db.update_record("partnermanager", {"id": manager_id}, update)

    async def _ensure_manager(self, manager_id: str):
        """Создаёт запись менеджера если не существует"""
        rows = await self.db.where(
            "partnermanager",
            filters=[{"column": "id", "value": manager_id}],
            limit=1
        )

        if not rows:
            await self.db.insert("partnermanager", {
                "id": manager_id,
                "points": 0,
                "new_partnerships": 0,
                "renewed_partnerships": 0,
                "is_active": True
            })

    async def get_manager_stats(self, manager_id: str, use_cache: bool = True) -> Dict[str, Any]:
        """Получает статистику менеджера"""
        if use_cache:
            cached = await self.stats_cache.get(manager_id)
            if cached:
                return cached

        await self._ensure_manager(manager_id)

        manager_rows = await self.db.where(
            "partnermanager",
            filters=[{"column": "id", "value": manager_id}],
            limit=1
        )
        manager = manager_rows[0] if manager_rows else None

        partnerships = await self.db.where(
            "partnership",
            filters=[{"column": "manager_id", "value": manager_id}]
        )

        servers = []
        for p in partnerships:
            last_renewal_dt = _time.ensure_datetime(p["last_renewal"])
            servers.append({
                "server_id": p["server_id"],
                "server_name": p["server_name"],
                "last_renewal": int(last_renewal_dt.timestamp()),
                "renewed_count": p["renewed_count"]
            })

        servers.sort(key=lambda x: x["last_renewal"], reverse=True)

        stats = {
            "points": manager["points"],
            "new_partnerships": manager["new_partnerships"],
            "renewed_partnerships": manager["renewed_partnerships"],
            "partnerships_count": len(partnerships),
            "servers": servers
        }

        if use_cache:
            await self.stats_cache.set(manager_id, stats)

        return stats

    async def get_user_points(self, user_id: str) -> int:
        """Получает баллы пользователя"""
        await self._ensure_manager(user_id)
        rows = await self.db.where(
            "partnermanager",
            filters=[{"column": "id", "value": user_id}],
            limit=1
        )
        return rows[0]["points"] if rows else 0

    async def update_pm_stats(self, user_id: str, points: int = 0):
        """Обновляет баллы (для системы наград)"""
        await self._ensure_manager(user_id)
        rows = await self.db.where(
            "partnermanager",
            filters=[{"column": "id", "value": user_id}],
            limit=1
        )

        if rows:
            new_points = rows[0]["points"] + points
            await self.db.update_record(
                "partnermanager",
                {"id": user_id},
                {"points": new_points}
            )
            await self.stats_cache.invalidate(user_id)

    async def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получает топ менеджеров"""
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

async def setup(bot):
    """Пустой setup для совместимости"""

