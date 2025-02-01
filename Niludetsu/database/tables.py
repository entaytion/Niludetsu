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
        
        # Таблица каналов-счетчиков
        "counter_channels": {
            "channel_id": "TEXT PRIMARY KEY",
            "last_number": "INTEGER DEFAULT 0",
            "updated_at": "DATETIME DEFAULT CURRENT_TIMESTAMP"
        },
        
        # Таблица профилей пользователей
        "user_profiles": {
            "user_id": "TEXT PRIMARY KEY",
            "name": "TEXT",
            "age": "INTEGER",
            "country": "TEXT",
            "bio": "TEXT",
            "timestamp": "DATETIME DEFAULT CURRENT_TIMESTAMP"
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
            "roles": "TEXT DEFAULT '[]'"
        },
        
        # Таблица временных каналов
        "temp_rooms": {
            "channel_id": "TEXT PRIMARY KEY",
            "guild_id": "TEXT",
            "owner_id": "TEXT",
            "name": "TEXT",
            "channel_type": "INTEGER",
            "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP"
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
        }
    }
    
    # Названия таблиц для удобного доступа
    TEMP_ROOMS = "temp_rooms"
    USERS = "users"
    ROLES = "roles"
    WARNINGS = "warnings"
    AFK = "afk"
    USER_PROFILES = "user_profiles"
    GIVEAWAYS = "giveaways"
    SHOP_ROLES = "shop_roles"
    
    # Колонки таблиц для удобного доступа
    COLUMNS = {
        TEMP_ROOMS: ["channel_id", "guild_id", "owner_id", "created_at", "name", "type", "parent_id", "limit_users", "is_locked", "allowed_users"],
        USERS: ["user_id", "balance", "deposit", "last_daily", "last_work", "last_rob", "xp", "level", "spouse", "marriage_date", "roles", "reputation", "messages_count", "voice_time", "voice_joins", "last_voice_join", "warnings", "is_banned", "ban_reason", "ban_time", "mute_time", "mute_reason", "notes", "created_at"],
        ROLES: ["role_id", "name", "balance", "description", "discord_role_id"],
        WARNINGS: ["id", "user_id", "guild_id", "moderator_id", "reason", "timestamp", "active"],
        AFK: ["user_id", "guild_id", "reason", "timestamp"],
        USER_PROFILES: ["user_id", "name", "age", "country", "bio", "timestamp"],
        GIVEAWAYS: ["giveaway_id", "channel_id", "message_id", "guild_id", "host_id", "prize", "winners_count", "end_time", "is_ended", "participants"],
        SHOP_ROLES: ["role_id", "price", "description", "purchases", "created_at"]
    }