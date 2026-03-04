"""
Модуль автомодерации для Niludetsu бота
Содержит менеджер настроек и правила проверки сообщений
"""

from .manager import AutoModManager
from .rules import AutoModRuleType, AutoModRule, LinksRule, InvitesRule, CapsLockRule, SpamRule, BadWordsRule, RepeatedTextRule, CustomWordsRule

__all__ = [
    "AutoModManager",
    "AutoModRuleType",
    "AutoModRule",
    "LinksRule",
    "InvitesRule",
    "CapsLockRule",
    "SpamRule",
    "BadWordsRule",
    "RepeatedTextRule",
    "CustomWordsRule"
]

