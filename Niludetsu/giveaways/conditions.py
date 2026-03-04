import json
from Niludetsu.database.supabase_database import database
from Niludetsu.tools.Time import TimeService
from typing import Any, Dict, Optional

_time = TimeService()

class GiveawayConditions:
    """Проверяем, соответствует ли участник условиям розыгрыша."""

    _VOICE_MINUTES_KEY = ("user_analytics", "voice_total")
    _LEVEL_KEY = ("users", "profile")

    @staticmethod
    def defaults() -> Dict[str, Any]:
        return {
            "min_server_time": 0,
            "min_voice_time": 0,
            "required_role": None,
            "min_level": 0,
            "booster_only": False,
            "no_revote": False,
        }

    @staticmethod
    async def _fetch_level(user_id: str, guild_id: str) -> int:
        row = await database.get_row("user_profile", user_id=user_id, guild_id=guild_id)
        return int(row.get("level", 0)) if row else 0

    @staticmethod
    async def _fetch_voice_minutes(user_id: str, guild_id: str) -> int:
        row = await database.get_row("user_analytics", user_id=user_id, guild_id=guild_id)
        return int(row.get("voice_total", 0) or 0) if row else 0

    @staticmethod
    async def _owns_role(member, guild, role_id: int) -> bool:
        if not guild:
            return False
        if hasattr(member, "roles"):
            return any(role.id == role_id for role in member.roles)
        guild_member = guild.get_member(member.id)
        return bool(guild_member and any(role.id == role_id for role in guild_member.roles))

    @staticmethod
    def _booster(member, guild) -> bool:
        if hasattr(member, "premium_since") and member.premium_since:
            return True
        if guild:
            gm = guild.get_member(member.id)
            return bool(gm and gm.premium_since)
        return False

    @staticmethod
    def _days_on_server(member) -> Optional[int]:
        joined = getattr(member, "joined_at", None)
        if not joined:
            return None
        joined_time = _time.ensure_datetime(joined)
        now = _time.now()
        return _time.seconds_between(joined_time, now) // 86400

    @staticmethod
    async def check(bot, member, payload: Dict[str, Any], guild=None) -> Dict[str, Any]:
        settings = {**GiveawayConditions.defaults(), **payload.get("settings", {})}
        guild = guild or getattr(member, "guild", None)

        if not member:
            return {"success": False, "reason": "Не удалось получить данные участника."}
        if member.bot:
            return {"success": False, "reason": "Боты не участвуют в розыгрышах."}

        host_id = str(payload.get("host_id") or "")
        if host_id and str(member.id) == host_id:
            return {"success": False, "reason": "Организатор не может участвовать в своём розыгрыше."}

        if guild and guild.owner_id == member.id:
            return {"success": False, "reason": "Владелец сервера не может участвовать в розыгрыше."}

        if settings["min_server_time"] > 0:
            days = GiveawayConditions._days_on_server(member)
            if days is None or days < settings["min_server_time"]:
                have = days if days is not None else "неизвестно"
                return {"success": False, "reason": f"Нужно быть на сервере {settings['min_server_time']} дн. (сейчас: {have})."}

        if settings["required_role"] and guild:
            role_id = int(settings["required_role"])
            if not await GiveawayConditions._owns_role(member, guild, role_id):
                role = guild.get_role(role_id)
                role_name = role.name if role else f"ID {role_id}"
                return {"success": False, "reason": f"Нужна роль {role_name}."}

        if settings["booster_only"] and not GiveawayConditions._booster(member, guild):
            return {"success": False, "reason": "Розыгрыш только для бустеров сервера."}

        if settings["min_voice_time"] > 0 and guild:
            voice_minutes = await GiveawayConditions._fetch_voice_minutes(str(member.id), str(guild.id))
            if voice_minutes < settings["min_voice_time"]:
                return {
                    "success": False,
                    "reason": f"Нужно {settings['min_voice_time']} минут в голосе (сейчас: {voice_minutes}).",
                }

        if settings["min_level"] > 0 and guild:
            level = await GiveawayConditions._fetch_level(str(member.id), str(guild.id))
            if level < settings["min_level"]:
                return {"success": False, "reason": f"Требуется уровень {settings['min_level']} (у вас: {level})."}

        return {"success": True, "reason": ""}

