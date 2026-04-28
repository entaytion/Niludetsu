from ..logging import logger

"""
QuestTracker — хуки для интеграции с существующими системами.

Подключается к:
  - on_message (через main.py)   → трекает сообщения
  - AnalyticsTracker              → трекает войс-минуты
  - BumpReminder                  → трекает бампы
"""

from Niludetsu.database import database

from Niludetsu.quests.manager import QuestManager

class QuestTracker:
    """Глобальный трекер квестов. Один на бота."""

    def __init__(self, bot=None):
        self.bot = bot
        self.manager = QuestManager(database)

    async def on_message(self, guild_id: str, user_id: str) -> None:
        """Вызывается при каждом сообщении."""
        try:
            await self.manager.increment_progress(
                user_id, guild_id, "messages", amount=1,
            )
        except Exception as exc:
            logger.exception(
                "QuestTracker.on_message failed (guild_id=%s, user_id=%s): %s",
                guild_id,
                user_id,
                exc,
            )

    async def on_voice_minute(self, guild_id: str, user_id: str, minutes: int = 1) -> None:
        """Вызывается когда юзер набирает минуту в войсе."""
        try:
            await self.manager.increment_progress(
                user_id, guild_id, "voice_minutes", amount=minutes,
            )
        except Exception as exc:
            logger.exception(
                "QuestTracker.on_voice_minute failed (guild_id=%s, user_id=%s, minutes=%s): %s",
                guild_id,
                user_id,
                minutes,
                exc,
            )

    async def on_bump(self, guild_id: str, user_id: str) -> None:
        """Вызывается при успешном бампе."""
        try:
            await self.manager.increment_progress(
                user_id, guild_id, "bump", amount=1,
            )
        except Exception as exc:
            logger.exception(
                "QuestTracker.on_bump failed (guild_id=%s, user_id=%s): %s",
                guild_id,
                user_id,
                exc,
            )
