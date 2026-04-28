from __future__ import annotations
from ...tools.Time import TimeService

import json
from typing import Any, Optional

from .base import BaseMixin

_time = TimeService()

class AnalyticsMixin(BaseMixin):
    async def get_analytics(self, user_id: str, guild_id: str) -> Optional[dict[str, Any]]:
        return await self.get_row("user_analytics", user_id=str(user_id), guild_id=str(guild_id))

    async def update_analytics(
        self,
        guild_id: str,
        user_id: str,
        *,
        add_messages: int = 0,
        add_deleted: int = 0,
        add_voice_seconds: int = 0,
        message_channel: Optional[str] = None,
        voice_channel: Optional[str] = None,
    ) -> dict[str, Any]:
        sql = """
            INSERT INTO public.user_analytics (guild_id, user_id, messages_total, messages_deleted, voice_seconds, message_channels, voice_channels, last_updated)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (guild_id, user_id) DO UPDATE SET
                messages_total = user_analytics.messages_total + EXCLUDED.messages_total,
                messages_deleted = user_analytics.messages_deleted + EXCLUDED.messages_deleted,
                voice_seconds = user_analytics.voice_seconds + EXCLUDED.voice_seconds,
                message_channels = CASE
                    WHEN $9::text IS NOT NULL THEN
                        jsonb_set(user_analytics.message_channels, ARRAY[$9::text],
                        (COALESCE(user_analytics.message_channels->>$9, '0')::int + $3)::text::jsonb)
                    ELSE user_analytics.message_channels
                END,
                voice_channels = CASE
                    WHEN $10::text IS NOT NULL THEN
                        jsonb_set(user_analytics.voice_channels, ARRAY[$10::text],
                        (COALESCE(user_analytics.voice_channels->>$10, '0')::int + $5)::text::jsonb)
                    ELSE user_analytics.voice_channels
                END,
                last_updated = EXCLUDED.last_updated
            RETURNING *;
        """

        msg_ch_init = {message_channel: add_messages} if message_channel else {}
        voice_ch_init = {voice_channel: add_voice_seconds} if voice_channel else {}

        row = await self._neon.fetchrow(
            sql,
            str(guild_id),
            str(user_id),
            add_messages,
            add_deleted,
            add_voice_seconds,
            msg_ch_init,
            voice_ch_init,
            _time.now(),
            message_channel,
            voice_channel,
        )
        return dict(row)
