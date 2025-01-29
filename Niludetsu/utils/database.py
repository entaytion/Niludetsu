import sqlite3
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

DB_PATH = 'config/database.db'

# --- DATABASE SCHEMAS ---
TABLES_SCHEMAS = {
    'users': '''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            balance INTEGER,
            deposit INTEGER,
            last_daily TEXT,
            last_work TEXT,
            last_rob TEXT,
            xp INTEGER,
            level INTEGER,
            spouse TEXT,
            marriage_date TEXT,
            roles TEXT DEFAULT '',
            reputation INTEGER DEFAULT 0,
            messages_count INTEGER DEFAULT 0,
            voice_time INTEGER DEFAULT 0,
            last_voice_update TEXT DEFAULT NULL
        )
    ''',
    'roles': '''
        CREATE TABLE IF NOT EXISTS roles (
            role_id INTEGER PRIMARY KEY,
            name TEXT,
            balance INTEGER,
            description TEXT,
            discord_role_id INTEGER
        )
    ''',
    'warnings': '''
        CREATE TABLE IF NOT EXISTS warnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            guild_id TEXT,
            moderator_id TEXT,
            reason TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            active BOOLEAN DEFAULT TRUE
        )
    ''',
    'afk': '''
        CREATE TABLE IF NOT EXISTS afk (
            user_id INTEGER,
            guild_id INTEGER,
            reason TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, guild_id)
        )
    ''',
    'user_profiles': '''
        CREATE TABLE IF NOT EXISTS user_profiles (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            age INTEGER,
            country TEXT,
            bio TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''',
    'user_streaks': '''
        CREATE TABLE IF NOT EXISTS user_streaks (
            user_id INTEGER PRIMARY KEY,
            streak_count INTEGER DEFAULT 0,
            last_message_date TIMESTAMP,
            total_messages INTEGER DEFAULT 0,
            highest_streak INTEGER DEFAULT 0
        )
    ''',
    'giveaways': '''
        CREATE TABLE IF NOT EXISTS giveaways (
            giveaway_id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id INTEGER NOT NULL,
            message_id INTEGER NOT NULL,
            guild_id INTEGER NOT NULL,
            host_id INTEGER NOT NULL,
            prize TEXT NOT NULL,
            winners_count INTEGER NOT NULL,
            end_time TEXT NOT NULL,
            is_ended INTEGER DEFAULT 0,
            participants TEXT DEFAULT "[]"
        )
    '''
}

def initialize_db() -> None:
    """Инициализация базы данных и создание необходимых таблиц"""
    if not os.path.exists('config'):
        os.makedirs('config')
        
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        for table_name, schema in TABLES_SCHEMAS.items():
            cursor.execute(schema)
            
            if table_name == 'users':
                # Проверяем существующие колонки
                cursor.execute("PRAGMA table_info(users)")
                existing_columns = {column[1] for column in cursor.fetchall()}
                
                # Список необходимых колонок и их типов
                required_columns = {
                    'messages_count': 'INTEGER DEFAULT 0',
                    'voice_time': 'INTEGER DEFAULT 0',
                    'roles': 'TEXT DEFAULT ""',
                    'xp': 'INTEGER DEFAULT 0',
                    'level': 'INTEGER DEFAULT 0'
                }
                
                # Добавляем отсутствующие колонки
                for column, column_type in required_columns.items():
                    if column not in existing_columns:
                        try:
                            cursor.execute(f'ALTER TABLE users ADD COLUMN {column} {column_type}')
                        except sqlite3.OperationalError:
                            pass  # Колонка уже существует
        
        conn.commit()

def initialize_table(table_name: str, schema: str) -> None:
    """Инициализация отдельной таблицы"""
    if not os.path.exists('config'):
        os.makedirs('config')
        
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(schema)
        conn.commit()

def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    """Получение данных пользователя из БД"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (str(user_id),))
        result = cursor.fetchone()
        
        if result:
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, result))
        return None

def save_user(user_id: int, user_data: Dict[str, Any]) -> None:
    """Сохранение данных пользователя в БД"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        columns = ', '.join(user_data.keys())
        placeholders = ', '.join(['?' for _ in user_data])
        values = tuple(user_data.values())
        
        query = f"""
        INSERT OR REPLACE INTO users (user_id, {columns})
        VALUES (?, {placeholders})
        """
        
        cursor.execute(query, (str(user_id),) + values)
        conn.commit()

def get_user_roles(user_id: int) -> List[int]:
    """Получение списка ролей пользователя"""
    user_data = get_user(user_id)
    if user_data and user_data.get('roles'):
        return json.loads(user_data['roles'])
    return []

def add_role_to_user(user_id: int, role_id: int) -> bool:
    """Добавление роли пользователю"""
    try:
        user_roles = get_user_roles(user_id)
        if role_id not in user_roles:
            user_roles.append(role_id)
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE users SET roles = ? WHERE user_id = ?",
                    (json.dumps(user_roles), str(user_id))
                )
                conn.commit()
        return True
    except Exception:
        return False

def remove_role_from_user(user_id: int, role_id: int) -> bool:
    """Удаление роли у пользователя"""
    try:
        user_roles = get_user_roles(user_id)
        if role_id in user_roles:
            user_roles.remove(role_id)
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE users SET roles = ? WHERE user_id = ?",
                    (json.dumps(user_roles), str(user_id))
                )
                conn.commit()
        return True
    except Exception:
        return False

def calculate_next_level_xp(level: int) -> int:
    """Расчет опыта для следующего уровня"""
    return 5 * (level ** 2) + 50 * level + 100

def get_roles() -> List[Dict[str, Any]]:
    """Получение списка всех ролей из БД"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM roles")
        roles = cursor.fetchall()
        
        if roles:
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, role)) for role in roles]
        return []

def get_role_by_id(role_id: int) -> Optional[Dict[str, Any]]:
    """Получение роли по ID из БД"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM roles WHERE role_id = ?", (role_id,))
        role = cursor.fetchone()
        
        if role:
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, role))
        return None

def save_role(role_data: Dict[str, Any]) -> bool:
    """Сохранение роли в БД"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            columns = ', '.join(role_data.keys())
            placeholders = ', '.join(['?' for _ in role_data])
            values = tuple(role_data.values())
            
            query = f"""
            INSERT OR REPLACE INTO roles ({columns})
            VALUES ({placeholders})
            """
            
            cursor.execute(query, values)
            conn.commit()
            return True
    except Exception:
        return False

def delete_role(role_id: int) -> bool:
    """Удаление роли из БД"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM roles WHERE role_id = ?", (role_id,))
            conn.commit()
            return True
    except Exception:
        return False

def format_voice_time(seconds: int) -> str:
    """Форматирование времени в голосовом канале"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    
    if hours > 0:
        return f"{hours} ч {minutes} мин"
    return f"{minutes} мин" 