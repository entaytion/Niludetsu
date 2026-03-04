from Niludetsu import Time
from Niludetsu.analytics.repository import AnalyticsRepository
from typing import Any, Dict, List, Optional, Tuple

_time = Time()

class AnalyticsManager:
    """Сервис для чтения агрегированной аналитики."""

    def __init__(self) -> None:
        self.repo = AnalyticsRepository()

    async def get_user_stats(self, guild_id: str, user_id: str) -> Dict[str, Any]:
        data = await self.repo.get_user_stats(guild_id, user_id)
        if not data:
            return {
                "messages": {"total": 0, "deleted": 0, "channels": {}},
                "voice": {"total_seconds": 0, "channels": {}},
            }

        return {
            "messages": {
                "total": int(data["messages_total"]),
                "deleted": int(data["messages_deleted"]),
                "channels": {k: int(v) for k, v in data["message_channels"].items()},
            },
            "voice": {
                "total_seconds": int(data["voice_seconds"]),
                "channels": {k: int(v) for k, v in data["voice_channels"].items()},
                "last_join": data["last_voice_join"],
            },
            "last_updated": data["last_updated"],
        }

    async def get_top_users(self, guild_id: str, *, limit: int = 10) -> Dict[str, List[Tuple[str, int]]]:
        return await self.repo.top_users(guild_id, limit=limit)

    async def get_server_stats(self, guild_id: str, *, limit: int = 10) -> Dict[str, Any]:
        totals = await self.repo.server_totals(guild_id)
        channels = await self.repo.top_channels(guild_id, limit=limit)
        return {**totals, "top_channels": channels}

