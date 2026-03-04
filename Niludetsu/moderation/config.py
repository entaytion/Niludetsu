import json
from typing import Dict, Any, Optional

class ActionType:
    """Типы действий модерации"""
    WARN = "warn"
    UNWARN = "unwarn"
    MUTE = "mute"
    UNMUTE = "unmute"
    BAN = "ban"
    UNBAN = "unban"

class ModerationConfig:
    """
    Класс для управления конфигурацией системы модерации.
    Содержит настройки наказаний для различных типов нарушений.
    """

    def __init__(self):
        from Niludetsu.moderation.automod.rules import AutoModRuleType

        # Настройки наказаний для автомодерации
        self.automod_punishment_settings = {
            AutoModRuleType.SPAM: {
                "duration": 45,               # Длительность мута в минутах
                "warn_duration": 1440,        # Длительность предупреждения в минутах (1 день)
                "issue_warning": True         # Выдавать ли предупреждение
            },
            AutoModRuleType.INVITES: {
                "duration": 1440,             # Мут на 1 день за инвайты
                "warn_duration": 1440,        # Предупреждение на 1 день
                "issue_warning": True,        # Выдавать предупреждение
                "ban": True                   # Применять бан вместо мута
            },
            AutoModRuleType.LINKS: {
                "duration": 30,                # 30 минут мута
                "warn_duration": 1440,        # Предупреждение на 1 день
                "issue_warning": True         # Выдавать предупреждение
            },
            AutoModRuleType.REPEATED_TEXT: {
                "duration": 30,                # 30 минут мута
                "warn_duration": 1440,        # Предупреждение на 1 день
                "issue_warning": True         # Выдавать предупреждение
            },
            AutoModRuleType.CAPS_LOCK: {
                "duration": 30,                # 30 минут мута
                "warn_duration": 1440,        # Предупреждение на 1 день
                "issue_warning": True         # Выдавать предупреждение
            },
            AutoModRuleType.BAD_WORDS: {
                "duration": 60,               # 60 минут мута
                "warn_duration": 1440,        # Предупреждение на 1 день
                "issue_warning": True         # Выдавать предупреждение
            },
            AutoModRuleType.CUSTOM_WORDS: {
                "duration": 1440,             # Мут на 1 день за повтор
                "warn_duration": 1440,        # Предупреждение на 1 день
                "issue_warning": True         # Выдавать предупреждение
            },
        }

        # Настройки прогрессии наказаний после накопления предупреждений
        self.warning_punishment_progression = {
            "1": {'type': ActionType.MUTE, 'duration': 10},       # 10 минут мута за 1 предупреждение
            "2": {'type': ActionType.MUTE, 'duration': 30},       # 30 минут мута за 2 предупреждения  
            "3": {'type': ActionType.MUTE, 'duration': 60},       # 1 час мута за 3 предупреждения
            "4": {'type': ActionType.BAN, 'duration': 30},    # 30 минут бана за 4 предупреждения
            "5": {'type': ActionType.BAN, 'duration': 60},    # 1 час бана за 5 предупреждений
        }

    def get_automod_punishment(self, rule_type) -> Dict[str, Any]:
        """
        Получает настройки наказания для конкретного типа правила автомодерации

        Args:
            rule_type: Тип правила автомодерации

        Returns:
            Dict: Словарь с настройками наказания
        """
        return self.automod_punishment_settings.get(rule_type, {
            "duration": 5,
            "warn_duration": 1440,
            "issue_warning": True
        })

    def get_warning_progression(self, warning_count: int) -> Dict[str, Any]:
        """
        Получает следующее наказание для пользователя на основе количества предупреждений

        Args:
            warning_count: Количество предупреждений

        Returns:
            Dict: Словарь с типом наказания и его длительностью
        """
        count_str = str(warning_count)
        # Если для такого количества предупреждений нет конфигурации, 
        # возвращаем конфигурацию для 5 предупреждений (максимальное)
        return self.warning_punishment_progression.get(count_str, 
                                                     self.warning_punishment_progression.get("5"))

# Создание глобального экземпляра конфигурации для использования в других модулях
moderation_config = ModerationConfig() 

