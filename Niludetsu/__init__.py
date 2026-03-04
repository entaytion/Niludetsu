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

__version__ = "agrentez-8"
__author__ = "Entaytion"
__license__ = "MIT"

Database = SupabaseDatabase  # ← алиас, чтобы импорт выглядел красиво
Time = TimeService
Loader = Loader

__all__ = [
    "database",
    "Database",
    "Time",
    "Loader",
    "Embed",
    "Colors",
    "Emojis",
    "InfoCard",
    "send",
    "defer",
    "send_moderation",
]

