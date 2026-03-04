from Niludetsu import Time
from Niludetsu.database.supabase_database import database
from typing import Any, Dict, List, Optional, Tuple

_time = Time()

class AnalyticsRepository:
    """Доступ к таблице user_analytics и агрегирующим запросам."""

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
        guild_id = str(guild_id)
        user_id = str(user_id)

        row = await self.db.get_row("user_analytics", guild_id=guild_id, user_id=user_id)
        if not row:
            row = await self.db.ensure_record(
                "user_analytics",
                guild_id=guild_id,
                user_id=user_id,
            )

        messages_total = max(int(row.get("messages_total") or 0) + add_messages, 0)
        messages_deleted = max(int(row.get("messages_deleted") or 0) + add_deleted, 0)
        voice_increment = max(int(add_voice_seconds), 0)
        voice_seconds = max(int(row.get("voice_seconds") or 0) + voice_increment, 0)

        message_channels = self._increment_channel_map(
            row.get("message_channels") or {},
            message_channel,
            add_messages,
        )
        voice_channels = self._increment_channel_map(
            row.get("voice_channels") or {},
            voice_channel,
            voice_increment,
        )

        payload = {
            "guild_id": guild_id,
            "user_id": user_id,
            "messages_total": messages_total,
            "messages_deleted": messages_deleted,
            "voice_seconds": voice_seconds,
            "message_channels": message_channels,
            "voice_channels": voice_channels,
            "last_updated": _time.to_iso(),
        }

        await self.db.upsert(
            "user_analytics",
            payload,
            on_conflict="user_id,guild_id",
        )

    async def set_last_voice_join(self, guild_id: str, user_id: str, value_iso: str | None) -> None:
        guild_id = str(guild_id)
        user_id = str(user_id)
        await self.db.update_record(
            "user_analytics",
            {"guild_id": guild_id, "user_id": user_id},
            {"last_voice_join": value_iso, "last_updated": _time.to_iso()},
            ensure_if_missing=True,
            ensure_params={"guild_id": guild_id, "user_id": user_id},
        )

    async def get_user_stats(self, guild_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        row = await self.db.get_row(
            "user_analytics",
            guild_id=str(guild_id),
            user_id=str(user_id),
        )
        return dict(row) if row else None

    async def top_users(
        self,
        guild_id: str,
        *,
        limit: int = 10,
    ) -> Dict[str, List[Tuple[str, int]]]:
        message_rows = await self.db.where(
            "user_analytics",
            columns=["user_id", "messages_total"],
            filters=[
                {"column": "guild_id", "value": str(guild_id)},
                {"column": "messages_total", "value": 0, "op": "gt"},
            ],
            order=[{"column": "messages_total", "ascending": False}],
            limit=limit,
        )
        voice_rows = await self.db.where(
            "user_analytics",
            columns=["user_id", "voice_seconds"],
            filters=[
                {"column": "guild_id", "value": str(guild_id)},
                {"column": "voice_seconds", "value": 0, "op": "gt"},
            ],
            order=[{"column": "voice_seconds", "ascending": False}],
            limit=limit,
        )
        return {
            "messages": [(row["user_id"], int(row["messages_total"])) for row in message_rows],
            "voice": [(row["user_id"], int(row["voice_seconds"])) for row in voice_rows],
        }

    async def server_totals(self, guild_id: str) -> Dict[str, int]:
        rows = await self.db.where(
            "user_analytics",
            filters=[{"column": "guild_id", "value": str(guild_id)}],
        )
        active_users = sum(
            1
            for row in rows
            if (row.get("messages_total") or 0) > 0 or (row.get("voice_seconds") or 0) > 0
        )
        total_messages = sum(int(row.get("messages_total") or 0) for row in rows)
        total_voice_seconds = sum(int(row.get("voice_seconds") or 0) for row in rows)
        return {
            "active_users": active_users,
            "total_messages": total_messages,
            "total_voice_seconds": total_voice_seconds,
        }

    async def top_channels(
        self,
        guild_id: str,
        *,
        limit: int = 10,
    ) -> Dict[str, List[Tuple[str, int]]]:
        rows = await self.db.where(
            "user_analytics",
            columns=["message_channels", "voice_channels"],
            filters=[{"column": "guild_id", "value": str(guild_id)}],
        )

        message_totals: Dict[str, int] = {}
        voice_totals: Dict[str, int] = {}

        for row in rows:
            for channel_id, count in (row.get("message_channels") or {}).items():
                message_totals[channel_id] = message_totals.get(channel_id, 0) + int(count)
            for channel_id, seconds in (row.get("voice_channels") or {}).items():
                voice_totals[channel_id] = voice_totals.get(channel_id, 0) + int(seconds)

        sorted_messages = sorted(message_totals.items(), key=lambda item: item[1], reverse=True)[:limit]
        sorted_voice = sorted(voice_totals.items(), key=lambda item: item[1], reverse=True)[:limit]

        return {
            "messages": sorted_messages,
            "voice": sorted_voice,
        }   

    @staticmethod
    def _increment_channel_map(
        original: Dict[str, int],
        channel_id: Optional[str],
        delta: int,
    ) -> Dict[str, int]:
        if not channel_id or delta <= 0:
            return dict(original)
        updated = dict(original)
        updated[channel_id] = updated.get(channel_id, 0) + delta
        return updated

