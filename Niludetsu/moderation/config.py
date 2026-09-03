from typing import Dict, Any

class ActionType:
    WARN = "warn"
    UNWARN = "unwarn"
    MUTE = "mute"
    UNMUTE = "unmute"
    BAN = "ban"
    UNBAN = "unban"

class ModerationConfig:

    def __init__(self):
        from Niludetsu.moderation.automod.rules import AutoModRuleType

        self.automod_punishment_settings = {
            AutoModRuleType.SPAM: {
                "duration": 45,
                "warn_duration": 1440,
                "issue_warning": True
            },
            AutoModRuleType.INVITES: {
                "duration": 1440,
                "warn_duration": 1440,
                "issue_warning": True,
                "ban": True
            },
            AutoModRuleType.LINKS: {
                "duration": 30,
                "warn_duration": 1440,
                "issue_warning": True
            },
            AutoModRuleType.REPEATED_TEXT: {
                "duration": 30,
                "warn_duration": 1440,
                "issue_warning": True
            },
            AutoModRuleType.CAPS_LOCK: {
                "duration": 30,
                "warn_duration": 1440,
                "issue_warning": True
            },
            AutoModRuleType.BAD_WORDS: {
                "duration": 60,
                "warn_duration": 1440,
                "issue_warning": True
            },
            AutoModRuleType.CUSTOM_WORDS: {
                "duration": 1440,
                "warn_duration": 1440,
                "issue_warning": True
            },
        }

        self.warning_punishment_progression = {
            "1": {'type': ActionType.MUTE, 'duration': 10},
            "2": {'type': ActionType.MUTE, 'duration': 30},
            "3": {'type': ActionType.MUTE, 'duration': 60},
            "4": {'type': ActionType.BAN, 'duration': 30},
            "5": {'type': ActionType.BAN, 'duration': 60},
        }

    def get_automod_punishment(self, rule_type) -> Dict[str, Any]:
        return self.automod_punishment_settings.get(rule_type, {
            "duration": 5,
            "warn_duration": 1440,
            "issue_warning": True
        })

    def get_warning_progression(self, warning_count: int) -> Dict[str, Any]:
        count_str = str(warning_count)
        return self.warning_punishment_progression.get(count_str, 
                                                     self.warning_punishment_progression.get("5"))

moderation_config = ModerationConfig() 

