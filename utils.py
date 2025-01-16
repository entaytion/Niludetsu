import discord
import sqlite3
import os
from discord import Embed, Colour
DB_PATH = 'config/database.db'

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

# --- EMOJIS ---
EMOJIS = {
    'DOT': '<:aeOutlineDot:1266066158029770833>',
    'MONEY': '<:aeMoney:1266066622561517781>',
    'SUCCESS': '<:aeSuccess:1266062451049365574>',
    'ERROR': '<:aeError:1266062540052365343>'
}

# --- FOOTERS ---
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
    if not os.path.exists('config'):
        os.makedirs('config')
        
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # --- USERS ---
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
                marriage_date TEXT,
                roles TEXT DEFAULT ''
            )
        ''')
        
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'roles' not in columns:
            cursor.execute('ALTER TABLE users ADD COLUMN roles TEXT DEFAULT ""')
        
        # --- ROLES ---
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

initialize_db()

def get_user(bot, user_id):
    member = bot.get_user(int(user_id))
    if member and member.bot and member.id != 1264591814208262154:
        return None
        
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        
        if user is None:
            cursor.execute('''
                INSERT INTO users (user_id, balance, deposit, last_daily, last_work, 
                                last_rob, xp, level, spouse, marriage_date, roles)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, 0, 0, None, None, None, 0, 0, None, None, ''))
            conn.commit()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            user = cursor.fetchone()
        
        return dict(zip([column[0] for column in cursor.description], user))

def save_user(user_id, user_data):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users
            SET balance = ?, deposit = ?, last_daily = ?, last_work = ?, 
                last_rob = ?, xp = ?, level = ?, spouse = ?, 
                marriage_date = ?, roles = ?
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
            user_data.get('roles', ''),
            user_id
        ))
        conn.commit()

def load_roles():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM roles')
        roles = cursor.fetchall()
        return [dict(zip([column[0] for column in cursor.description], role)) for role in roles]

def get_role_by_id(role_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM roles WHERE role_id = ?', (role_id,))
        role = cursor.fetchone()
        if role:
            return dict(zip([column[0] for column in cursor.description], role))
        return None
    
def count_role_owners(role_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM users 
            WHERE roles LIKE ? 
            OR roles LIKE ? 
            OR roles LIKE ?
            OR roles = ?
        ''', (
            f'%,{role_id},%',  # роль в середині списку
            f'{role_id},%',    # роль на початку списку
            f'%,{role_id}',    # роль в кінці списку
            f'{role_id}'       # тільки одна роль
        ))
        return cursor.fetchone()[0]
    
def get_user_roles(user_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT roles FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        if result and result[0]:
            # Фільтруємо пусті значення та конвертуємо в int
            return [int(role_id) for role_id in result[0].split(',') if role_id.strip()]
        return []
    
def add_role_to_user(user_id, role_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        current_roles = get_user_roles(user_id)
        
        if role_id not in current_roles:
            current_roles.append(role_id)
            new_roles = ','.join(map(str, current_roles))
            
            cursor.execute('''
                UPDATE users 
                SET roles = ? 
                WHERE user_id = ?
            ''', (new_roles, user_id))
            conn.commit()
            return True
        return False
    
def remove_role_from_user(user_id, role_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        current_roles = get_user_roles(user_id)
        
        if role_id in current_roles:
            current_roles.remove(role_id)
            new_roles = ','.join(map(str, current_roles)) if current_roles else ''
            
            cursor.execute('''
                UPDATE users 
                SET roles = ? 
                WHERE user_id = ?
            ''', (new_roles, user_id))
            conn.commit()
            return True
        return False
    
# --- LEVELING ---
def calculate_next_level_xp(level):
    if level == 0:
        return 100
    elif level >= 100:
        return float('inf')
    else:
        return int(calculate_next_level_xp(level - 1) * 1.5)