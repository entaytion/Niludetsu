from typing import Dict, List

class Tables:
    """Схемы таблиц базы данных"""
    
    SCHEMA = {
        "moderation": {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "user_id": "TEXT",                                    # ID пользователя (null для исключений каналов)
            "channel_id": "TEXT",                                 # ID канала (для исключений автомодерации)
            "guild_id": "TEXT NOT NULL",                         # ID сервера
            "moderator_id": "TEXT",                              # ID модератора (null для автомодерации)
            "type": "TEXT NOT NULL",                             # Тип: warn/mute/ban/violation/exception
            "rule_name": "TEXT",                                 # Название нарушенного правила
            "reason": "TEXT",                                    # Причина наказания
            "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",  # Дата создания
            "expires_at": "DATETIME",                           # Дата окончания (для временных наказаний)
            "active": "BOOLEAN DEFAULT TRUE",                    # Активно ли наказание
            "INDEXES": [
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_moderation_exception ON moderation(channel_id, rule_name) WHERE type = 'exception'"
            ]
        },
        
        "automod_exceptions": {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "channel_id": "TEXT NOT NULL",                      # ID канала
            "rule_name": "TEXT NOT NULL",                       # Название правила
            "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP", # Дата создания
            "INDEXES": [
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_automod_exceptions ON automod_exceptions(channel_id, rule_name)"
            ]
        },
        "afk": {
            "user_id": "TEXT",
            "guild_id": "TEXT",
            "reason": "TEXT",
            "timestamp": "DATETIME DEFAULT CURRENT_TIMESTAMP",
            "PRIMARY KEY": "(user_id, guild_id)"
        },
        
        "users": {
            "user_id": "TEXT PRIMARY KEY",
            "reputation": "INTEGER DEFAULT 0",
            "balance": "INTEGER DEFAULT 0",
            "premium_balance": "INTEGER DEFAULT 0",
            "deposit": "INTEGER DEFAULT 0",
            "xp": "INTEGER DEFAULT 0",
            "level": "INTEGER DEFAULT 1",
            "voice_time": "INTEGER DEFAULT 0",
            "voice_joins": "INTEGER DEFAULT 0",
            "last_voice_join": "DATETIME",
            "messages_count": "INTEGER DEFAULT 0",
            "last_daily": "DATETIME",
            "last_work": "DATETIME",
            "last_voice_update": "DATETIME",
            "roles": "TEXT DEFAULT '[]'",
            "name": "TEXT",
            "birthday": "TEXT",
            "country": "TEXT",
            "bio": "TEXT",
            "timestamp": "DATETIME DEFAULT CURRENT_TIMESTAMP"
        },
        
        "temp_rooms": {
            "channel_id": "TEXT PRIMARY KEY",
            "guild_id": "TEXT NOT NULL",
            "owner_id": "TEXT NOT NULL",
            "name": "TEXT NOT NULL",
            "channel_type": "INTEGER DEFAULT 2",
            "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
            "trusted_users": "TEXT DEFAULT '[]'",
            "banned_users": "TEXT DEFAULT '[]'",
            "region": "TEXT",
            "bitrate": "INTEGER DEFAULT 64000",
            "user_limit": "INTEGER DEFAULT 0",
            "is_locked": "BOOLEAN DEFAULT FALSE",
            "is_hidden": "BOOLEAN DEFAULT FALSE",
            "thread_id": "TEXT"
        },
        
        "giveaways": {
            "giveaway_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "channel_id": "TEXT",
            "message_id": "TEXT UNIQUE",
            "guild_id": "TEXT",
            "host_id": "TEXT",
            "prize": "TEXT",
            "winners_count": "INTEGER",
            "end_time": "DATETIME",
            "is_ended": "INTEGER DEFAULT 0",
            "participants": "TEXT DEFAULT '[]'"
        },
        
        "shop_roles": {
            "role_id": "TEXT PRIMARY KEY",
            "price": "INTEGER NOT NULL",
            "description": "TEXT",
            "purchases": "INTEGER DEFAULT 0",
            "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP"
        },
        
        "global_bans": {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "banned_user_id": "TEXT NOT NULL",
            "owner_id": "TEXT NOT NULL",
            "timestamp": "DATETIME DEFAULT CURRENT_TIMESTAMP",
            "UNIQUE": "(banned_user_id, owner_id)"
        },
        
        "games": {
            "channel_id": "TEXT PRIMARY KEY",
            "game_type": "TEXT NOT NULL",  # 'counter' или 'words'
            "last_value": "TEXT DEFAULT ''",  # для counter - число, для words - слово
            "used_values": "TEXT DEFAULT ''",  # для words - использованные слова
            "forum_id": "TEXT",  # ID форум-канала (для counter)
            "thread_id": "TEXT",  # ID ветки (для counter)
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        },
        
        "automod_rules": {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "rule_name": "TEXT NOT NULL",                       # Название правила
            "guild_id": "TEXT NOT NULL",                        # ID сервера
            "enabled": "BOOLEAN DEFAULT TRUE",                  # Включено/выключено
            "settings": "TEXT",                                 # JSON с настройками
            "last_update": "DATETIME DEFAULT CURRENT_TIMESTAMP",# Последнее обновление
            "INDEXES": [
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_automod_rules ON automod_rules(rule_name, guild_id)"
            ]
        }
    }
    
    # Названия таблиц для удобного доступа
    TEMP_ROOMS = "temp_rooms"
    USERS = "users"
    MODERATION = "moderation"
    AFK = "afk"
    GIVEAWAYS = "giveaways"
    SHOP_ROLES = "shop_roles"
    GAMES = "games"
    AUTOMOD_RULES = "automod_rules"
    
    # Колонки таблиц для удобного доступа
    COLUMNS = {
        TEMP_ROOMS: ["channel_id", "guild_id", "owner_id", "created_at", "name", "type", "parent_id", "limit_users", "is_locked", "allowed_users"],
        USERS: ["user_id", "reputation", "balance", "premium_balance", "deposit", "xp", "level", "voice_time", "voice_joins", "last_voice_join", "messages_count", "last_daily", "last_work", "last_voice_update", "roles", "name", "birthday", "country", "bio", "timestamp"],
        MODERATION: ["id", "user_id", "channel_id", "guild_id", "moderator_id", "type", "rule_name", "reason", "created_at", "expires_at", "active"],
        AFK: ["user_id", "guild_id", "reason", "timestamp"],
        GIVEAWAYS: ["giveaway_id", "channel_id", "message_id", "guild_id", "host_id", "prize", "winners_count", "end_time", "is_ended", "participants"],
        SHOP_ROLES: ["role_id", "price", "description", "purchases", "created_at"],
        GAMES: ["channel_id", "game_type", "last_value", "used_values", "forum_id", "thread_id", "created_at", "updated_at"],
        AUTOMOD_RULES: ["id", "rule_name", "guild_id", "enabled", "settings", "last_update"]
    }