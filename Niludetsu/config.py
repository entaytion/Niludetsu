"""
config.py — тепер ПРОКСІ поверх settings (БД).

Всі старі `from Niludetsu.config import FOO` і `config.FOO` продовжують
працювати — просто тепер вони тягнуть значення з Neon (через settings-кеш),
а не з хардкоду.

⚠ Якщо БД ще не заповнена або settings.load() ще не викликався —
  повертаємо hardcoded defaults нижче як fallback.
"""
from __future__ import annotations
from typing import Any


# ── Fallback defaults (якщо БД порожня або settings не завантажений) ──

_DEFAULTS: dict[str, Any] = {
    "PREFIX": {
        "MAIN_SERVER": ["!", "?", ".", "*", "+", ",", "-", ":", ";", "<", "=", ">", "_", "~"],
        "OTHER_SERVER": ["ae!", "ae?", "ae."],
    },
    "SERVERS": {
        "MAIN_ID": 1125344221587574866,
        "ALLOWED_ID": [
            1355942675479658637,
            1356171837486137434,
            1351206119670022245,
            1375564755871203388,
            1381892749787271269,
        ],
    },
    "OWNER_ID": 636570363605680139,

    # Канали
    "NOTIFICATION_CHANNEL_ID": 1414934353087303720,
    "STARBOARD_CHANNEL_ID": 1347917939017388253,
    "LOG_CHANNEL_ID": 1350056714031988736,
    "BUGS_CHANNEL_ID": 1379055355572523019,
    "INVITES_CHANNEL_ID": 1130114236673171476,
    "FREE_GAMES_CHANNEL_ID": 1338873365183594600,

    # Налаштування
    "STARBOARD_MIN_STARS": 1,
    "STARBOARD_EMOJI": "⭐",
    "VERIFICATION_ENABLED": True,

    # Ролі (склад)
    "BAN_ROLE_ID": 1346899133365227610,
    "PARTNER_MANAGER_ID": 1125344222065725543,
    "EVENT_MANAGER_ID": 1401652941265309838,
    "JUNIOR_MODERATOR_ID": 1125344222065725545,
    "MODERATOR_ID": 1333425575133450241,
    "SENIOR_MODERATOR_ID": 1401661504901746699,
    "ADMIN_MODERATOR_ID": 1401653709498482818,
    "ADMINISTRATOR_ID": 1130108216211157112,
    "SERVER_TEAM_ID": 1125344222007005188,
    "EVENT_TEAM_ID": 1401652665884213348,
    "PM_TEAM_ID": 1401653467625426984,
    "MODER_TEAM_ID": 1401652356277469408,
    "ROLE_PRIORITY": {
        1125344222065725545: 1,  # Junior Mod
        1333425575133450241: 2,  # Moderator
        1401661504901746699: 3,  # Senior Mod
        1401653709498482818: 4,  # Admin Mod
        1130108216211157112: 5,  # Administrator
    },
    "GIVEAWAY_ROLE": 1401652665884213348,

    # Тимчасові канали
    "TEMPROOM_CATEGORY": 1414740540314091621,
    "TEMPROOM_CHANNEL": 1422520098534592553,
    "TEMPROOM_VOICE": 1422520569181765795,
    "TEMPROOM_MESSAGE": 1425605817947783239,
    "TEMPROOM_DEFAULT_NAME": "🔊 {name}",
    "TEMPROOM_INVITE_LIFETIME": 86400,
    "TEMPROOM_THREAD_CATEGORY": None,

    # Ролі (панелі)
    "GENDER_ROLES": [
        {"emoji": "♂️", "id": 1125344221960872004, "name": "♂️"},
        {"emoji": "♀️", "id": 1125344221960872003, "name": "♀️"},
        {"emoji": "❔", "id": 1125344221960872002, "name": "❔"},
    ],
    "COLOR_ROLES": [
        {"color": 16711680, "emoji": "❤️", "id": 1338100752299851776, "name": "❤️"},
        {"color": 16738740, "emoji": "🩷", "id": 1338100761141444661, "name": "🩷"},
        {"color": 16753920, "emoji": "🧡", "id": 1338100760088412210, "name": "🧡"},
        {"color": 16776960, "emoji": "💛", "id": 1338100753167945841, "name": "💛"},
        {"color": 65280,    "emoji": "💚", "id": 1338100753751080992, "name": "💚"},
        {"color": 255,      "emoji": "💙", "id": 1338100755311231046, "name": "💙"},
        {"color": 65535,    "emoji": "🩵", "id": 1338100759178514453, "name": "🩵"},
        {"color": 8388736,  "emoji": "💜", "id": 1338100758205169686, "name": "💜"},
        {"color": 10824234, "emoji": "🤎", "id": 1338106700321919036, "name": "🤎"},
        {"color": 1,        "emoji": "🖤", "id": 1338100757404319824, "name": "🖤"},
        {"color": 8421504,  "emoji": "🩶", "id": 1338100762273775726, "name": "🩶"},
        {"color": 16777215, "emoji": "🤍", "id": 1338100756028592233, "name": "🤍"},
    ],
    "OPTIONAL_ROLES": [
        {"id": 1364498609340416040, "name": "Новости",   "description": "Уведомления о новостях",    "emoji": "📰"},
        {"id": 1364498617758388245, "name": "Розыгрыши", "description": "Уведомления о розыгрышах",  "emoji": "🎁"},
    ],
}


# ── Проксі-об'єкт ──────────────────────────────────────────────────────

class _ConfigProxy:
    """
    Проксі який при зверненні до атрибута:
    1. Шукає в settings._cache (Neon DB, завантажено при старті).
    2. Якщо не знайдено — бере з _DEFAULTS (hardcoded fallback).
    """

    def __getattr__(self, key: str) -> Any:
        if key.startswith("_"):
            raise AttributeError(key)
        try:
            from Niludetsu.settings import settings
            val = settings._cache.get(key)
            if val is not None:
                return val
        except Exception:
            pass
        if key in _DEFAULTS:
            return _DEFAULTS[key]
        raise AttributeError(f"config has no attribute '{key}'")

    def __setattr__(self, key: str, value: Any) -> None:
        # Синхронний set — тільки в settings кеш.
        # Для запису в БД використовуй: await settings.set(key, value)
        try:
            from Niludetsu.settings import settings
            settings._cache[key] = value
        except Exception:
            pass

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self.__getattr__(key)
        except AttributeError:
            return default


# Єдиний екземпляр — замінює старий модульний стиль
_proxy = _ConfigProxy()

# Це дозволяє робити `from Niludetsu.config import SERVERS` через __getattr__ на рівні модуля
def __getattr__(key: str) -> Any:
    return _proxy.__getattr__(key)
