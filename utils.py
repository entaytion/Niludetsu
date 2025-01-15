import discord
import sqlite3
import os
from discord import Embed, Colour

USERS_DB = 'config/users.db'
ROLES_DB = 'config/roles.db'

# --- EMBEDS ---
def create_embed(title=None, description=None, color=0xf20c3c, fields=None, footer=None, image_url=None, author=None, url=None, timestamp=None):
    embed = Embed(title=title, description=description, colour=Colour(color))
    if fields:
        for field in fields:
            embed.add_field(name=field.get('name'), value=field.get('value'), inline=field.get('inline', False))
    if footer:
        embed.set_footer(text=footer.get('text'), icon_url=footer.get('icon_url'))
    if image_url:
        embed.set_image(url=image_url)
    if author:
        embed.set_author(name=author.get('name'), icon_url=author.get('icon_url'), url=author.get('url'))
    if url:
        embed.url = url
    if timestamp:
        embed.timestamp = timestamp
    return embed

FOOTER_SUCCESS = {
    'text': "Операция выполнена успешно.",
    'icon_url': "https://cdn.discordapp.com/emojis/1266062451049365574.webp?size=64&quality=lossless"
}

FOOTER_ERROR = {
    'text': "Операция не выполнена успешно.",
    'icon_url': "https://cdn.discordapp.com/emojis/1266062540052365343.webp?size=64&quality=lossless"
}

# --- DATABASE ---
def initialize_db():
    if not os.path.exists(USERS_DB):
        with sqlite3.connect(USERS_DB) as conn:
            cursor = conn.cursor()
            cursor.execute('''
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
                    marriage_date TEXT
                )
            ''')
            conn.commit()
initialize_db()

def get_user(bot, user_id):
    member = bot.get_user(int(user_id))
    if member and member.bot and member.id != 1264591814208262154:
        return None  # Если это бот, вернем None
        
    with sqlite3.connect(USERS_DB) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        
        if user is None:
            cursor.execute('''
                INSERT INTO users (user_id, balance, deposit, last_daily, last_work, last_rob, xp, level, spouse, marriage_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                0,  # Начальное значение balance
                0,  # Начальное значение deposit
                None,  # Начальное значение last_daily
                None,  # Начальное значение last_work
                None,  # Начальное значение last_rob
                0,  # Начальное значение xp
                0,   # Начальное значение level
                None,  # Начальное значение spouse
                None   # Начальное значение marriage_date
            ))
            conn.commit()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            user = cursor.fetchone()
        
        return dict(zip([column[0] for column in cursor.description], user))

def save_user(user_id, user_data):
    with sqlite3.connect(USERS_DB) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users
            SET balance = ?, deposit = ?, last_daily = ?, last_work = ?, last_rob = ?, xp = ?, level = ?, spouse = ?, marriage_date = ?
            WHERE user_id = ?
        ''', (
            user_data.get('balance', 0),
            user_data.get('deposit', 0),
            user_data.get('last_daily', None),
            user_data.get('last_work', None),
            user_data.get('last_rob', None),
            user_data.get('xp', 0),
            user_data.get('level', 0),
            user_data.get('spouse', None),
            user_data.get('marriage_date', None),
            user_id
        ))
        conn.commit()

# Создание базы данных и таблицы ролей
def initialize_db_roles():
    if not os.path.exists(ROLES_DB):
        with sqlite3.connect(ROLES_DB) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS roles (
                    role_id INTEGER PRIMARY KEY,
                    name TEXT,
                    balance INTEGER,
                    description TEXT,
                    discord_role_id INTEGER
                )
            ''')
            conn.commit()
initialize_db_roles()

# Метод для получения всех ролей
def load_roles():
    with sqlite3.connect(ROLES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM roles')
        roles = cursor.fetchall()
        return [dict(zip([column[0] for column in cursor.description], role)) for role in roles]

# Метод для получения роли по ID
def get_role_by_id(role_id):
    with sqlite3.connect(ROLES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM roles WHERE role_id = ?', (role_id,))
        role = cursor.fetchone()
  
        if role:
            return dict(zip([column[0] for column in cursor.description], role))
        return None

# --- LEVELING ---
def calculate_next_level_xp(level):
    if level == 0:
        return 100
    elif level >= 100:
        return float('inf')
    else:
        return int(calculate_next_level_xp(level - 1) * 1.5)
