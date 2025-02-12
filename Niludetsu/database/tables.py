from typing import Dict, List

class Tables:
    """Схемы таблиц базы данных"""
    
    SCHEMA = {
        # Таблица предупреждений
        "warnings": {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "user_id": "TEXT NOT NULL",
            "guild_id": "TEXT NOT NULL",
            "moderator_id": "TEXT NOT NULL",
            "reason": "TEXT NOT NULL",
            "timestamp": "DATETIME DEFAULT CURRENT_TIMESTAMP",
            "active": "BOOLEAN DEFAULT TRUE"
        },
        
        # Таблица нарушений автомодерации
        "automod_violations": {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "user_id": "TEXT NOT NULL",
            "rule_name": "TEXT NOT NULL",
            "violations_count": "INTEGER DEFAULT 1",
            "last_violation": "DATETIME DEFAULT CURRENT_TIMESTAMP",
            "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "DATETIME DEFAULT CURRENT_TIMESTAMP"
        },
        
        # Таблица исключений автомодерации
        "automod_exceptions": {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "channel_id": "TEXT NOT NULL",
            "rule_name": "TEXT NOT NULL",
            "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
            "UNIQUE": "(channel_id, rule_name)"
        },
        
        # Таблица каналов-счетчиков
        "counter_channels": {
            "channel_id": "TEXT PRIMARY KEY",
            "last_number": "INTEGER DEFAULT 0",
            "updated_at": "DATETIME DEFAULT CURRENT_TIMESTAMP"
        },
        
        # Таблица AFK статусов
        "afk": {
            "user_id": "TEXT",
            "guild_id": "TEXT",
            "reason": "TEXT",
            "timestamp": "DATETIME DEFAULT CURRENT_TIMESTAMP",
            "PRIMARY KEY": "(user_id, guild_id)"
        },
        
        # Таблица пользователей
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
        
        # Таблица временных каналов
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
        
        # Таблица розыгрышей
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
        
        # Таблица магазина ролей
        "shop_roles": {
            "role_id": "TEXT PRIMARY KEY",
            "price": "INTEGER NOT NULL",
            "description": "TEXT",
            "purchases": "INTEGER DEFAULT 0",
            "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP"
        },
        
        # Таблица глобальных банов
        "global_bans": {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "banned_user_id": "TEXT NOT NULL",
            "owner_id": "TEXT NOT NULL",
            "timestamp": "DATETIME DEFAULT CURRENT_TIMESTAMP",
            "UNIQUE": "(banned_user_id, owner_id)"
        },
        
        # Таблица каналов для игры в слова
        "words_channels": {
            "channel_id": "TEXT PRIMARY KEY",
            "last_word": "TEXT DEFAULT ''",
            "used_words": "TEXT DEFAULT ''", 
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        }
    }
    
    # Названия таблиц для удобного доступа
    TEMP_ROOMS = "temp_rooms"
    USERS = "users"
    ROLES = "roles"
    WARNINGS = "warnings"
    AFK = "afk"
    GIVEAWAYS = "giveaways"
    SHOP_ROLES = "shop_roles"
    WORDS_CHANNELS = "words_channels"
    AUTOMOD_VIOLATIONS = "automod_violations"
    AUTOMOD_EXCEPTIONS = "automod_exceptions"
    
    # Колонки таблиц для удобного доступа
    COLUMNS = {
        TEMP_ROOMS: ["channel_id", "guild_id", "owner_id", "created_at", "name", "type", "parent_id", "limit_users", "is_locked", "allowed_users"],
        USERS: ["user_id", "reputation", "balance", "premium_balance", "deposit", "xp", "level", "voice_time", "voice_joins", "last_voice_join", "messages_count", "last_daily", "last_work", "last_voice_update", "roles", "name", "birthday", "country", "bio", "timestamp"],
        ROLES: ["role_id", "name", "balance", "description", "discord_role_id"],
        WARNINGS: ["id", "user_id", "guild_id", "moderator_id", "reason", "timestamp", "active"],
        AFK: ["user_id", "guild_id", "reason", "timestamp"],
        GIVEAWAYS: ["giveaway_id", "channel_id", "message_id", "guild_id", "host_id", "prize", "winners_count", "end_time", "is_ended", "participants"],
        SHOP_ROLES: ["role_id", "price", "description", "purchases", "created_at"],
        WORDS_CHANNELS: ["channel_id", "last_word", "used_words", "created_at", "updated_at"],
        AUTOMOD_VIOLATIONS: ["id", "user_id", "rule_name", "violations_count", "last_violation", "created_at", "updated_at"],
        AUTOMOD_EXCEPTIONS: ["id", "channel_id", "rule_name", "created_at"]
    }