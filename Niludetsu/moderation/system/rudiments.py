from ...tools.Embed import Embed
from ...tools.Emojis import Emojis
from ...tools.Time import TimeService
"""Универсальная система для просмотра наказаний (rudiments)."""

import discord, math

from dataclasses import dataclass
from Niludetsu.moderation.config import ActionType
from Niludetsu.moderation.manager import ModerationManager

from typing import Dict, Iterable, List, Optional

_time = TimeService()

@dataclass(frozen=True)
class RudimentRecord:

    rudiment: str
    user_id: int
    moderator_id: Optional[int]
    action_type: str
    reason: str
    active: bool
    duration_minutes: Optional[int]
    created_at: Optional[object]
    expires_at: Optional[object]
    metadata: Dict[str, object]

    @property
    def created_timestamp(self) -> Optional[int]:
        dt = _time.ensure_datetime(self.created_at)
        return int(dt.timestamp()) if dt else None

    @property
    def expires_timestamp(self) -> Optional[int]:
        dt = _time.ensure_datetime(self.expires_at)
        return int(dt.timestamp()) if dt else None

class RudimentsSystem:

    _ACTION_ALIASES: Dict[str, str] = {
        "warn": ActionType.WARN,
        "warns": ActionType.WARN,
        "warning": ActionType.WARN,
        "mute": ActionType.MUTE,
        "mutes": ActionType.MUTE,
        "timeout": ActionType.MUTE,
        "ban": ActionType.BAN,
        "bans": ActionType.BAN,
    }

    _ACTION_LABELS: Dict[str, str] = {
        ActionType.WARN: "Предупреждение",
        ActionType.MUTE: "Мут",
        ActionType.BAN: "Бан",
    }

    _ACTION_EMOJIS: Dict[str, str] = {
        ActionType.WARN: Emojis.WARN,
        ActionType.MUTE: Emojis.MUTE,
        ActionType.BAN: Emojis.BAN,
    }

    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.manager: ModerationManager = getattr(bot, "moderation_manager", None) or ModerationManager(bot)

    def normalize_action(self, action: Optional[str]) -> Optional[str]:
        if not action:
            return None
        lowered = action.lower()
        if lowered in ("all", "*", "any"):
            return None
        return self._ACTION_ALIASES.get(lowered) or self._ACTION_ALIASES.get(lowered.rstrip("s"))

    async def fetch_records(
        self,
        *,
        member: Optional[discord.Member] = None,
        action: Optional[str] = None,
        include_inactive: bool = False,
        rudiment: Optional[str] = None,
    ) -> List[RudimentRecord]:

        normalized_action = self.normalize_action(action)

        if rudiment:
            record = await self.manager.get_punishment_by_rudiment(str(rudiment))
            if not record:
                return []
            normalized = self._normalize_record(record)
            if member and normalized.user_id != member.id:
                return []
            if normalized_action and normalized.action_type != normalized_action:
                return []
            return [normalized]

        if member is None:
            raise ValueError("member должен быть передан, если не указан rudiment")

        records: List[RudimentRecord] = []
        action_pool: Iterable[Optional[str]]

        if normalized_action:
            action_pool = (normalized_action,)
        else:
            action_pool = (ActionType.WARN, ActionType.MUTE, ActionType.BAN)

        for action_type in action_pool:
            if include_inactive:
                punishments = await self.manager.get_all_punishments(
                    user_id=member.id,
                    action_type=action_type,
                    include_inactive=True,
                )
            else:
                punishments = await self.manager.get_active_punishments(
                    user_id=member.id,
                    action_type=action_type,
                )
            records.extend(self._normalize_record(entry) for entry in punishments)

        records.sort(key=lambda rec: rec.created_timestamp or 0, reverse=True)

        return records

    def _normalize_record(self, raw: Dict[str, object]) -> RudimentRecord:
        def _to_int(value: object) -> Optional[int]:
            try:
                return int(value) if value is not None else None
            except (TypeError, ValueError):
                return None

        duration = _to_int(raw.get("duration"))
        return RudimentRecord(
            rudiment=str(raw.get("rudiment", "?")),
            user_id=_to_int(raw.get("user_id")) or 0,
            moderator_id=_to_int(raw.get("moderator_id")),
            action_type=str(raw.get("type", "")).lower(),
            reason=(str(raw.get("reason")) or "Не указана").strip(),
            active=bool(raw.get("active", False)),
            duration_minutes=duration if duration and duration > 0 else None,
            created_at=raw.get("created_at"),
            expires_at=raw.get("expires_at"),
            metadata=raw.get("metadata") or {},
        )

    def build_list_embed(
        self,
        *,
        member: discord.Member,
        records: List[RudimentRecord],
        action: Optional[str],
        include_inactive: bool,
        page: int,
        per_page: int,
    ) -> Embed:

        title_suffix = self._ACTION_LABELS.get(action or "", "Нарушения") if action else "Нарушения"
        title = f"{Emojis.MODERATION} {title_suffix}".strip()

        total = len(records)
        total_pages = max(1, math.ceil(total / per_page))
        current_page = max(1, min(page, total_pages))

        if total:
            start = (current_page - 1) * per_page
            end = start + per_page
            page_records = records[start:end]
            if page_records:
                description = "\n\n".join(self._format_record_line(record) for record in page_records)
            else:
                description = "Нарушения не найдены"
        else:
            description = "Нарушения не найдены"

        embed = Embed.default(
            title=title,
            description=description
        )
        embed.set_thumbnail(url=member.display_avatar.url)

        footer_parts = [f"Всего: {total}"]
        if total_pages > 1:
            footer_parts.append(f"Страница {current_page}/{total_pages}")
        embed.set_footer(text=" • ".join(footer_parts))

        return embed

    def build_single_embed(
        self,
        *,
        guild: discord.Guild,
        record: RudimentRecord
    ) -> Embed:

        action_emoji = self._ACTION_EMOJIS.get(record.action_type, "📘")
        status_emoji = "🟢" if record.active else "⚪"
        status_text = "Активен" if record.active else "Завершен"

        title = f"{action_emoji} ``#{record.rudiment}`` • {status_emoji} {status_text}"

        user = guild.get_member(record.user_id)
        user_text = user.mention if user else f"`ID: {record.user_id}`"

        moderator = guild.get_member(record.moderator_id) if record.moderator_id else None
        moderator_text = moderator.mention if moderator else (f"`ID: {record.moderator_id}`" if record.moderator_id else "Не указан")

        created_text = self._format_timestamp(record.created_timestamp)

        description_parts = [
            f"**Пользователь:** {user_text}",
            f"**Модератор:** {moderator_text}",
            f"",
            f"**Причина:**",
            f"> {record.reason}",
            f"",
            f"**Выдано:** {created_text}",
        ]

        if record.expires_timestamp:
            expires_text = self._format_timestamp(record.expires_timestamp)
            description_parts.append(f"**Истекает:** {expires_text}")

        if record.duration_minutes:
            duration_text = self._format_duration(record.duration_minutes)
            description_parts.append(f"**Длительность:** {duration_text}")

        embed = Embed.default(
            title=title,
            description="\n".join(description_parts)
        )

        if user and user.display_avatar:
            embed.set_thumbnail(url=user.display_avatar.url)

        return embed

    def _format_record_line(self, record: RudimentRecord) -> str:
        emoji = self._ACTION_EMOJIS.get(record.action_type, "📘")
        status_emoji = "🟢" if record.active else "⚪"
        status_text = "Активен" if record.active else "Завершен"

        moderator = self._format_moderator(record.moderator_id)
        created = self._format_timestamp_short(record.created_timestamp)

        header = f"{emoji} **``#{record.rudiment}``** • {status_emoji} {status_text}"

        details = [
            f"> **Модератор:** {moderator}",
            f"> **Причина:** {record.reason}",
            f"> **Выдано:** {created}",
        ]

        if record.duration_minutes:
            duration = self._format_duration(record.duration_minutes)
            details.append(f"> **Длительность:** {duration}")

        if record.active and record.expires_timestamp:
            expires = self._format_timestamp_short(record.expires_timestamp)
            details.append(f"> **Истекает:** {expires}")

        return header + "\n" + "\n".join(details)

    def _format_moderator(self, moderator_id: Optional[int]) -> str:
        if not moderator_id:
            return "Не указан"
        return f"<@{moderator_id}>"

    @staticmethod
    def _format_timestamp(value: Optional[int]) -> Optional[str]:
        if not value:
            return None
        return f"<t:{value}:R> • <t:{value}:f>"

    @staticmethod
    def _format_timestamp_short(value: Optional[int]) -> Optional[str]:
        if not value:
            return None
        return f"<t:{value}:R>"

    @staticmethod
    def _format_duration(duration_minutes: Optional[int]) -> str:
        if not duration_minutes:
            return "Не указана"
        seconds = max(duration_minutes, 0) * 60
        return _time.format_duration(seconds)

__all__ = ("RudimentsSystem", "RudimentRecord",)

