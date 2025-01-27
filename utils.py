import discord
from discord import app_commands
import sqlite3
import os
from discord import Embed, Colour
from functools import wraps

DB_PATH = 'config/database.db'

# --- EMBEDS ---
def create_embed(title=None, description=None, color='DEFAULT', fields=None, footer=None, image_url=None, author=None, url=None, timestamp=None, thumbnail_url=None):
    try:
        # Если color это строка, пытаемся получить цвет из COLORS
        if isinstance(color, str):
            color = COLORS.get(color.upper(), COLORS['DEFAULT'])
            
        embed = Embed(title=title, description=description, colour=Colour(color))
        
        if fields:
            for field in fields:
                if not all(key in field for key in ['name', 'value']):
                    continue
                embed.add_field(
                    name=field['name'],
                    value=field['value'], 
                    inline=field.get('inline', False)
                )
                
        if footer:
            if isinstance(footer, dict):
                embed.set_footer(
                    text=footer.get('text', ''),
                    icon_url=footer.get('icon_url', '')
                )
            else:
                print(f"⚠️ Помилка: footer має бути словником, отримано {type(footer)}. Footer: {footer}")
                
        if image_url:
            embed.set_image(url=image_url)
            
        if thumbnail_url:
            embed.set_thumbnail(url=thumbnail_url)
            
        if author and isinstance(author, dict):
            embed.set_author(
                name=author.get('name'),
                icon_url=author.get('icon_url'),
                url=author.get('url')
            )
            
        if url:
            embed.url = url
            
        if timestamp:
            embed.timestamp = timestamp
            
        return embed
        
    except Exception as e:
        print(f"⚠️ Помилка при створенні ембеду: {str(e)}")
        return Embed(description="Помилка при створенні ембеду", colour=Colour(COLORS['RED']))

# --- EMOJIS ---
EMOJIS = {
    # --- MAIN ---
    'DOT': '<:BotDot:1266063532517232701>',
    'MONEY': '<:BotMoney:1266063131457880105>',
    'SUCCESS': '<:BotOk:1266062451049365574>',
    'ERROR': '<:BotError:1266062540052365343>',
    'INFO': '<:BotInfo:1332835368365719592>',
    'WARNING': '<:BotWarning:1332836101487984781>',
    # --- STREAK ---
    'FLAME': '<:BotFlame:1332836327137349642>',
    # --- TEMP VOICES ---
    'VoiceCrown': '<:VoiceCrown:1332417411370057781>',
    'VoiceUsers': '<:VoiceUsers:1332418260435603476>',
    'VoiceNumbers': '<:VoiceNumbers:1332418493915725854>',
    'VoiceLock': '<:VoiceLock:1332418712304615495>',
    'VoiceEdit': '<:VoiceEdit:1332418910242471967>',
    'VoiceVisible': '<:VoiceVisible:1332419077184163920>',
    'VoiceKick': '<:VoiceKick:1332419383003447427>',
    'VoiceMute': '<:VoiceMute:1332419509830553601>',
    'VoiceBitrate': '<:VoiceBitrate:1332419630672904294>',
    # --- ANALYTICS ---
    'STATS': '<:AnalyticsStats:1332731704015847455>',
    'INFO': '<:AnalyticsInfo:1332731894491779164>',
    'MEMBERS': '<:AnalyticsMembers:1332732020991721502>',
    'BOOST': '<:AnalyticsBoost:1332732537956466698>',
    'SHIELD': '<:AnalyticsSecurity:1332732698611023882>',
    'FEATURES': '<:AnalyticsFeature:1332732366812221440>',
    'CHANNELS': '<:AnalyticsChannels:1332732203242750092>',
    'SETTINGS': '<:AnalyticsSettings:1332732862004461638>',
    'OTHER': '<:AnalyticsOther:1332731704015847455>',
    'PC': '<:AnalyticsPC:1332733064375177288>',
    'LINK': '<:AnalyticsLink:1332733206956474478>',
    'ROLES': '<:AnalyticsRoles:1332733459893846089>',
    'CROWN': '<:AnalyticsCrown:1332733632896303186>',
    'BOT': '<:AnalyticsBot:1332734596449697823>',
    # --- STREAK INFO ---
    'CALENDAR': '<:BotCalendar:1332836632449257525>',
    'MESSAGE': '<:BotMessages:1332836789383073893>',
    'STATUS': '<:BotStatus:1332837240929255464>',
    'CLOCK': '<:BotClock:1332837421603360799>',
    # --- 2048 ---
    '2048_0': '<:2048_0:1333180087083991111>',
    '2048_2': '<:2048_2:1333180133258956882>',
    '2048_4': '<:2048_4:1333180162950565979>',
    '2048_8': '<:2048_8:1333180190855270400>',
    '2048_16': '<:2048_16:1333180223763775662>',
    '2048_32': '<:2048_32:1333180256516837376>',
    '2048_64': '<:2048_64:1333180298145435719>',
    '2048_128': '<:2048_128:1333180326436016208>',
    '2048_256': '<:2048_256:1333180358891409440>',
    '2048_512': '<:2048_512:1333180385277902858>',
    '2048_1024': '<:2048_1024:1333180415619629179>',
    '2048_2048': '<:2048_2048:1333180450402996378>',
}
# --- COLORS ---
COLORS = {
    'DEFAULT': 0xf20c3c,  # Добавляем дефолтный цвет
    'GREEN': 0x30f20c,
    'YELLOW': 0xf1f20c,
    'RED': 0xf20c3c,
    'BLUE': 0x0c3ef2,
    'WHITE': 0xFFFFFF,
    'BLACK': 0x000000
}

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
            reputation INTEGER DEFAULT 0
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
            user_id INTEGER,
            guild_id INTEGER,
            moderator_id INTEGER,
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

def initialize_db():
    if not os.path.exists('config'):
        os.makedirs('config')
        
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # Инициализируем все таблицы
        for table_name, schema in TABLES_SCHEMAS.items():
            cursor.execute(schema)
            
            # Специальная проверка для таблицы users
            if table_name == 'users':
                cursor.execute("PRAGMA table_info(users)")
                columns = [column[1] for column in cursor.fetchall()]
                if 'roles' not in columns:
                    cursor.execute('ALTER TABLE users ADD COLUMN roles TEXT DEFAULT ""')
        
        conn.commit()

def initialize_table(table_name, schema):
    if not os.path.exists('config'):
        os.makedirs('config')
        
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(schema)
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