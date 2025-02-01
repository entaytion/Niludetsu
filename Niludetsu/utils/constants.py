from typing import Dict, List, Union

# Цвета для эмбедов
class Colors:
    PRIMARY = 0xf20c3c   # Стандартный цвет.
    ERROR = 0xdf5e60      # Красный
    WARNING = 0xd2c16b    # Жёлтый
    SUCCESS = 0x6bd277    # Зелёный
    INFO = 0x6b7ad2       # Синий

# Эмодзи для разных состояний и действий
class Emojis:
    @staticmethod
    def combine(*emojis: Union[str, 'Emojis']) -> str:
        """
        Объединяет несколько эмодзи в одну строку
        
        Пример:
        >>> Emojis.combine(Emojis.SUCCESS, Emojis.ERROR, "<:custom:123456>")
        "✅❌<:custom:123456>"
        """
        return ''.join(str(emoji) for emoji in emojis) 

    # Эмодзи для состояний.
    ERROR = "<:BotStatusError:1334479369833287682>"
    WARNING = "<:BotStatusWarning:1334479450951122954>"
    SUCCESS = "<:BotStatusSuccess:1334479519612010537>"
    INFO = "<:BotStatusInfo:1334479584447696936>"
    LOADING = "🔄"
    ARROW_RIGHT = "➡️"
    ARROW_LEFT = "⬅️"
    STAR = "⭐"
    CROWN = "👑"
    SETTINGS = "⚙️"
    MEMBERS = "👥"
    TIME = "⏰"
    VOICE = "🔊"
    TEXT = "💭"
    PLUS = "➕"
    MINUS = "➖"