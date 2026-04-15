"""
Niludetsu - библиотека для создания Discord бота.
Основной функционал, работа с серверами, музыка, игры, API, и многое другое.
"""

from .database.supabase_database import SupabaseDatabase, database
from .tools.Embed import Embed, Colors
from .tools.Emojis import Emojis
from .tools.InfoCard import InfoCard
from .tools.Loader import Loader
from .tools.Time import TimeService
from .tools.SendHybrid import send, defer, send_moderation
from .tools.Discord import resolve_member, safe_edit, safe_delete, safe_fetch_user, safe_fetch_message, delete_after, owner_check
from .tools.GameView import GameView

__version__ = "agrentez-9"
__author__ = "Entaytion"
__license__ = "MIT"

Database = SupabaseDatabase  # ← алиас, чтобы импорт выглядел красиво
Time = TimeService
Loader = Loader

import Niludetsu.Exceptions as Exceptions

__all__ = [
    "database",
    "Database",
    "Time",
    "Loader",
    "Exceptions",
    "Embed",
    "Colors",
    "Emojis",
    "InfoCard",
    "send",
    "defer",
    "send_moderation",
    "resolve_member",
    "safe_edit",
    "safe_delete",
    "safe_fetch_user",
    "safe_fetch_message",
    "delete_after",
    "owner_check",
    "GameView",
]

