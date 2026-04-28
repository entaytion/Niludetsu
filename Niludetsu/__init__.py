"""
Niludetsu - библиотека для создания Discord бота.
"""

from .database import Database, database
from .economy.manager import EconomyManager
from .quests.manager import QuestManager
from .quests.tracker import QuestTracker
from .levels.manager import LevelManager
from .levels.tracker import LevelTracker
from .moderation.manager import ModerationManager
from .marriage.marriage_manager import MarriageManager
from .marriage.adoption_manager import AdoptionManager
from .achievements.manager import AchievementsManager
from .analytics.manager import AnalyticsManager
from .analytics.tracker import AnalyticsTracker
from .development.Webhooks import Webhooks
from .moderation.automod.manager import AutoModManager
from .moderation.automod.rules import AutoModRuleType, RuleConfig, build_rule

from .tools.Embed import Embed, Colors
from .tools.Emojis import Emojis
from .tools.Time import TimeService
from .tools.SendHybrid import send, defer, send_moderation
from .tools.Discord import resolve_member, safe_edit, safe_delete, safe_fetch_message, safe_fetch_user, delete_after
from .tools.InfoCard import InfoCard
from .tools.Patterns import PatternChecker
from .tools.AccessControl import AccessGuard

from .embeds.Economy import EconomyEmbed
from .embeds.Achievements import AchievementEmbed

from .moderation.config import ActionType
from .moderation.exceptions import ModerationError
from .moderation.checks import check_moderation_target
from .moderation.embed import moderationembed

from .logging import logger
from . import config
from .settings import settings

__version__ = "agrentez-10"
__author__ = "Entaytion"

Time = TimeService

import Niludetsu.Exceptions as Exceptions

__all__ = [
    # Database
    "database", "Database",
    # Managers
    "EconomyManager", "QuestManager", "QuestTracker", "LevelManager", "LevelTracker",
    "ModerationManager", "AutoModManager", "AutoModRuleType", "RuleConfig", "build_rule",
    "MarriageManager", "AdoptionManager",
    "AchievementsManager", "AnalyticsManager", "AnalyticsTracker",
    "Webhooks",
    # Tools
    "Embed", "Colors", "Emojis", "TimeService", "Time",
    "send", "defer", "send_moderation",
    "resolve_member", "safe_edit", "safe_delete", "safe_fetch_message",
    "safe_fetch_user", "delete_after", "InfoCard", "PatternChecker", "AccessGuard",
    # Embeds
    "EconomyEmbed", "AchievementEmbed",
    # Moderation helpers
    "ActionType", "ModerationError", "check_moderation_target", "moderationembed",
    # System
    "logger", "config", "settings", "Exceptions",
]
