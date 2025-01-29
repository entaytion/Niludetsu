import sqlite3
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

DB_PATH = 'config/database.db'

def get_db_connection():
    """Создает и возвращает соединение с базой данных"""
    return sqlite3.connect(DB_PATH)

# --- DATABASE SCHEMAS ---
TABLES_SCHEMAS = {
    'temp_rooms': '''
        CREATE TABLE IF NOT EXISTS temp_rooms (
            channel_id TEXT PRIMARY KEY,
            guild_id TEXT,
            owner_id TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            name TEXT,
            type INTEGER,
            parent_id TEXT,
            limit_users INTEGER DEFAULT 0,
            is_locked BOOLEAN DEFAULT 0,
            allowed_users TEXT DEFAULT '[]'
        )
    ''',
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
            voice_joins INTEGER DEFAULT 0,
            last_voice_join REAL DEFAULT NULL,
            warnings INTEGER DEFAULT 0,
            is_banned BOOLEAN DEFAULT 0,
            ban_reason TEXT DEFAULT NULL,
            ban_time INTEGER DEFAULT NULL,
            mute_time INTEGER DEFAULT NULL,
            mute_reason TEXT DEFAULT NULL,
            notes TEXT DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

def create_tables():
    """Создание и обновление таблиц в базе данных"""
    conn = get_db_connection()
    cursor = conn.cursor()

    for table_name, schema in TABLES_SCHEMAS.items():
        # Создаем таблицу если её нет
        cursor.execute(schema)
        
        # Получаем список существующих столбцов
        cursor.execute(f"PRAGMA table_info({table_name})")
        existing_columns = {column[1] for column in cursor.fetchall()}
        
        # Извлекаем определения столбцов из схемы
        column_definitions = schema.split('\n')[2:-2]
        
        for column_def in column_definitions:
            column_def = column_def.strip().strip(',')
            if column_def and not column_def.startswith('PRIMARY KEY'):
                # Извлекаем имя столбца
                column_name = column_def.split()[0]
                
                # Пропускаем первичные ключи и составные ограничения
                if column_name == 'PRIMARY' or ',' in column_name:
                    continue
                
                # Если столбец не существует, добавляем его
                if column_name not in existing_columns:
                    try:
                        # Для временных меток используем текущее время как константное значение
                        if 'CURRENT_TIMESTAMP' in column_def or 'DATETIME' in column_def:
                            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            column_def = column_def.replace('DEFAULT CURRENT_TIMESTAMP', f"DEFAULT '{current_time}'")
                            column_def = column_def.replace('TIMESTAMP', 'TEXT')
                            column_def = column_def.replace('DATETIME', 'TEXT')
                        
                        alter_query = f"ALTER TABLE {table_name} ADD COLUMN {column_def}"
                        cursor.execute(alter_query)
                        print(f"✅ Добавлен столбец {column_name} в таблицу {table_name}")
                    except sqlite3.OperationalError as e:
                        print(f"⚠️ Ошибка при добавлении столбца {column_name}: {e}")

    conn.commit()
    conn.close()

def add_temp_room(channel_id: str, guild_id: str, owner_id: str, name: str, channel_type: int, parent_id: str = None, limit_users: int = 0) -> bool:
    """Добавление временной приватной комнаты в базу данных"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO temp_rooms (channel_id, guild_id, owner_id, name, type, parent_id, limit_users)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (channel_id, guild_id, owner_id, name, channel_type, parent_id, limit_users))
            conn.commit()
            return True
    except Exception as e:
        print(f"Ошибка при добавлении временной комнаты: {e}")
        return False

def get_temp_room(channel_id: str) -> Optional[Dict[str, Any]]:
    """Получение информации о временной приватной комнате"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM temp_rooms WHERE channel_id = ?", (channel_id,))
            result = cursor.fetchone()
            
            if result:
                columns = [description[0] for description in cursor.description]
                room_data = dict(zip(columns, result))
                # Преобразуем строку allowed_users в список
                if 'allowed_users' in room_data:
                    room_data['allowed_users'] = json.loads(room_data['allowed_users'])
                return room_data
            return None
    except Exception as e:
        print(f"Ошибка при получении временной комнаты: {e}")
        return None

def remove_temp_room(channel_id: str) -> bool:
    """Удаление временной приватной комнаты из базы данных"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM temp_rooms WHERE channel_id = ?", (channel_id,))
            conn.commit()
            return True
    except Exception as e:
        print(f"Ошибка при удалении временной комнаты: {e}")
        return False

def get_user_temp_rooms(owner_id: str) -> List[Dict[str, Any]]:
    """Получение всех временных приватных комнат пользователя"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM temp_rooms WHERE owner_id = ?", (owner_id,))
            results = cursor.fetchall()
            
            if results:
                columns = [description[0] for description in cursor.description]
                rooms = []
                for row in results:
                    room_data = dict(zip(columns, row))
                    # Преобразуем строку allowed_users в список
                    if 'allowed_users' in room_data:
                        room_data['allowed_users'] = json.loads(room_data['allowed_users'])
                    rooms.append(room_data)
                return rooms
            return []
    except Exception as e:
        print(f"Ошибка при получении временных комнат пользователя: {e}")
        return []

def update_temp_room(channel_id: str, **kwargs) -> bool:
    """Обновление параметров временной приватной комнаты"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Если обновляем список разрешенных пользователей, преобразуем его в JSON
            if 'allowed_users' in kwargs:
                kwargs['allowed_users'] = json.dumps(kwargs['allowed_users'])
            
            # Формируем SET часть запроса
            set_clause = ', '.join([f"{k} = ?" for k in kwargs.keys()])
            values = tuple(kwargs.values()) + (channel_id,)
            
            query = f"UPDATE temp_rooms SET {set_clause} WHERE channel_id = ?"
            cursor.execute(query, values)
            conn.commit()
            return True
    except Exception as e:
        print(f"Ошибка при обновлении временной комнаты: {e}")
        return False

def is_temp_room_owner(channel_id: str, user_id: str) -> bool:
    """Проверка, является ли пользователь владельцем временной комнаты"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT owner_id FROM temp_rooms WHERE channel_id = ?", (channel_id,))
            result = cursor.fetchone()
            return result is not None and result[0] == user_id
    except Exception as e:
        print(f"Ошибка при проверке владельца комнаты: {e}")
        return False 