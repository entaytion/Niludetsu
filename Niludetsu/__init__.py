"""
Niludetsu - библиотека для создания Discord бота.
Основной функционал, работа с серверами, музыка, игры, API, и многое другое.
"""

# --- Версия и информация ---
__version__ = "alpha-1"
__author__ = "Entaytion"
__license__ = "GNU General Public License v3.0"

# --- База данных ---
from .database import (
    Database,
    Tables,
    TableSchema,
    Column,
    Index
)

# --- Утилиты ---
from .utils.embed import Embed
from .utils.constants import Colors, Emojis
from .utils.cog_loader import CogLoader
from .utils.config_loader import BotState, LoggingState
from .utils.command_sync import CommandSync
from .utils.setup_manager import SetupManager
from .utils.settings import Settings

# --- Ядро ---
from .core import (
    TempRoomsManager,
    LevelSystem,
    LoggingState,
    BaseLogger
)

# --- Аналитика ---
from .analytics import (
    BotAnalytics,
    ServerAnalytics,
    RolesAnalytics,
    ChannelsAnalytics,
    MessageAnalytics
)

# --- API интеграции ---
from .api import (
    AkinatorAPI,
    CurrencyAPI,
    GifsAPI,
    TranslateAPI,
    WeatherAPI
)

# --- Логирование ---
from .logging import (
    ApplicationLogger,
    AutoModLogger,
    ChannelLogger,
    EmojiLogger,
    EntitlementLogger,
    ErrorLogger,
    EventLogger,
    InviteLogger,
    MessageLogger,
    PollLogger,
    RoleLogger,
    ServerLogger,
    SoundboardLogger,
    StageLogger,
    StickerLogger,
    ThreadLogger,
    UserLogger,
    VoiceLogger,
    WebhookLogger
)

# --- Модерация ---
from .moderation import (
    ModPermissions,
    has_permission,
    admin_only,
    mod_only,
    helper_only,
    cooldown
)

# --- Музыка ---
from .music import (
    Music,
    VoiceState,
    Song
)

# --- Профиль ---
from .profile import (
    ProfileManager,
    ProfileData,
    ProfileImage
)

__all__ = [
    # База данных
    "Database",
    "Tables",
    "TableSchema",
    "Column",
    "Index",
    
    # Утилиты
    "Embed",
    "Colors",
    "Emojis",
    "CogLoader",
    "BotState",
    "CommandSync",
    "SetupManager",
    "LoggingState",
    "Settings",
    
    # Основные компоненты
    "TempRoomsManager",
    "LevelSystem",
    "LoggingState",
    "BaseLogger",
    
    # Модерация
    "ModPermissions",
    "has_permission",
    "admin_only",
    "mod_only",
    "helper_only",
    "cooldown",
    
    # Аналитика
    "BotAnalytics",
    "ServerAnalytics",
    "RolesAnalytics",
    "ChannelsAnalytics",
    "MessageAnalytics",
    
    # API интеграции
    "AkinatorAPI",
    "CurrencyAPI",
    "GifsAPI",
    "TranslateAPI",
    "WeatherAPI",
    
    # Логирование
    "ApplicationLogger",
    "AutoModLogger",
    "ChannelLogger",
    "EmojiLogger",
    "EntitlementLogger",
    "ErrorLogger",
    "EventLogger",
    "InviteLogger",
    "MessageLogger",
    "PollLogger",
    "RoleLogger",
    "ServerLogger",
    "SoundboardLogger",
    "StageLogger",
    "StickerLogger",
    "ThreadLogger",
    "UserLogger",
    "VoiceLogger",
    "WebhookLogger",
    
    # Музыка
    "Music",
    "VoiceState",
    "Song",
    
    # Профиль
    "ProfileManager",
    "ProfileData",
    "ProfileImage"
] 