from ..tools.Time import TimeService

from Niludetsu.database import database

from typing import Any, Dict, List, Optional, Tuple

_time = TimeService()

class AnalyticsRepository:
    """Оптимізований репозиторій аналітики під Neon SQL агрегацію."""

    def __init__(self) -> None:
        self.db = database

    async def upsert_user_row(
        self,
        guild_id: str,
        user_id: str,
        *,
        add_messages: int = 0,
        add_deleted: int = 0,
        add_voice_seconds: float = 0.0,
        message_channel: Optional[str] = None,
        voice_channel: Optional[str] = None,
    ) -> None:
        await self.db.update_analytics(
            guild_id=guild_id,
            user_id=user_id,
            add_messages=add_messages,
            add_deleted=add_deleted,
            add_voice_seconds=int(add_voice_seconds),
            message_channel=message_channel,
            voice_channel=voice_channel
        )

    async def set_last_voice_join(self, guild_id: str, user_id: str, value_iso: str | None) -> None:
        new_row = await self.db.update_record(
            "user_analytics",
            where={"guild_id": str(guild_id), "user_id": str(user_id)},
            values={"last_voice_join": value_iso, "last_updated": _time.now()},
            ensure_if_missing=True,
            ensure_params={"guild_id": str(guild_id), "user_id": str(user_id)},
        )
        if new_row:
            await self.db.update_user_cache(str(user_id), str(guild_id), "analytics", new_row)

    async def get_user_stats(self, guild_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        return await self.db.get_analytics(user_id, guild_id)

    async def top_users(self, guild_id: str, *, limit: int = 10) -> Dict[str, List[Tuple[str, int]]]:
        # Використовуємо універсальний where з Database (тут вже було ок, але підстрахуємося)
        m_rows = await self.db.where(
            "user_analytics",
            columns=["user_id", "messages_total"],
            filters=[{"column": "guild_id", "value": str(guild_id)}, {"column": "messages_total", "value": 0, "op": "gt"}],
            order=[{"column": "messages_total", "ascending": False}],
            limit=limit
        )
        v_rows = await self.db.where(
            "user_analytics",
            columns=["user_id", "voice_seconds"],
            filters=[{"column": "guild_id", "value": str(guild_id)}, {"column": "voice_seconds", "value": 0, "op": "gt"}],
            order=[{"column": "voice_seconds", "ascending": False}],
            limit=limit
        )
        return {
            "messages": [(r["user_id"], int(r["messages_total"])) for r in m_rows],
            "voice": [(r["user_id"], int(r["voice_seconds"])) for r in v_rows],
        }

    async def server_totals(self, guild_id: str) -> Dict[str, int]:
        # ОПТИМІЗАЦІЯ: Агрегація на рівні БД
        query = """
            SELECT 
                COUNT(*) FILTER (WHERE messages_total > 0 OR voice_seconds > 0) as active_users,
                SUM(messages_total) as total_messages,
                SUM(voice_seconds) as total_voice_seconds
            FROM public.user_analytics
            WHERE guild_id = $1
        """
        row = await self.db._neon.fetchrow(query, str(guild_id))
        if not row:
            return {"active_users": 0, "total_messages": 0, "total_voice_seconds": 0}
        
        return {
            "active_users": row["active_users"] or 0,
            "total_messages": int(row["total_messages"] or 0),
            "total_voice_seconds": int(row["total_voice_seconds"] or 0),
        }

    async def top_channels(self, guild_id: str, *, limit: int = 10) -> Dict[str, List[Tuple[str, int]]]:
        # ОПТИМІЗАЦІЯ: Розпаковка JSONB масиву на рівні БД
        msg_query = """
            SELECT key, SUM(value::int) as total
            FROM public.user_analytics, jsonb_each_text(message_channels)
            WHERE guild_id = $1
            GROUP BY key
            ORDER BY total DESC
            LIMIT $2
        """
        voice_query = """
            SELECT key, SUM(value::int) as total
            FROM public.user_analytics, jsonb_each_text(voice_channels)
            WHERE guild_id = $1
            GROUP BY key
            ORDER BY total DESC
            LIMIT $2
        """
        
        m_rows = await self.db._neon.fetch(msg_query, str(guild_id), limit)
        v_rows = await self.db._neon.fetch(voice_query, str(guild_id), limit)
        
        return {
            "messages": [(r["key"], int(r["total"])) for r in m_rows],
            "voice": [(r["key"], int(r["total"])) for r in v_rows],
        }
