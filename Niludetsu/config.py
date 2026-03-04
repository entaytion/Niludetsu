# Настройка серверов 
PREFIX = {
    "MAIN_SERVER": ["!", "?", ".", "*", "+", ",", "-", ":", ";", "<", "=", ">", "_", "~"],
    "OTHER_SERVER": ["ae!", "ae?", "ae."]
}
SERVERS = {
    "MAIN_ID": 1125344221587574866,
    "ALLOWED_ID": [1355942675479658637, 1356171837486137434, 1351206119670022245, 1375564755871203388, 1381892749787271269]
}
OWNER_ID = 636570363605680139

# Каналы 
NOTIFICATION_CHANNEL_ID = 1414934353087303720
IDEAS_CHANNEL_ID = 1125546993763237929
STARBOARD_CHANNEL_ID = 1347917939017388253
LOG_CHANNEL_ID = 1350056714031988736
BUGS_CHANNEL_ID = 1379055355572523019
INVITES_CHANNEL_ID = 1130114236673171476
FREE_GAMES_CHANNEL_ID = 1338873365183594600

# Настройки 
STARBOARD_MIN_STARS = 1
STARBOARD_EMOJI = "⭐"
VERIFICATION_ENABLED = True

# Роли Æther! (состав) 
BAN_ROLE_ID = 1346899133365227610
PARTNER_MANAGER_ID = 1125344222065725543
EVENT_MANAGER_ID = 1401652941265309838
JUNIOR_MODERATOR_ID = 1125344222065725545
MODERATOR_ID = 1333425575133450241
SENIOR_MODERATOR_ID = 1401661504901746699
ADMIN_MODERATOR_ID = 1401653709498482818
ADMINISTRATOR_ID = 1130108216211157112
SERVER_TEAM_ID = 1125344222007005188
EVENT_TEAM_ID = 1401652665884213348
PM_TEAM_ID = 1401653467625426984
MODER_TEAM_ID = 1401652356277469408
ROLE_PRIORITY = {
    JUNIOR_MODERATOR_ID: 1,     # Младший модератор
    MODERATOR_ID: 2,            # Модератор
    SENIOR_MODERATOR_ID: 3,     # Старший модератор
    ADMIN_MODERATOR_ID: 4,      # Админ-модератор (без кулдауна)
    ADMINISTRATOR_ID: 5         # Администратор (без кулдауна)
}
# Роли Æther! (прочее) 
GIVEAWAY_ROLE = 1401652665884213348

# Настройка временных каналов 
TEMPROOM_CATEGORY: int | None = 1414740540314091621  # категория, куда складываются временные голосовые
TEMPROOM_CHANNEL: int | None = 1422520098534592553   # текстовый канал, где висит интерфейс
TEMPROOM_VOICE: int | None = 1422520569181765795     # лобби/кнопка: заходишь — создаётся персональный канал
TEMPROOM_MESSAGE: int | None = 1425605817947783239   # ID сообщения с меню управления (если None — пропускаем привязку)
TEMPROOM_DEFAULT_NAME: str = "🔊 {name}"            # шаблон названия (используется при создании)
TEMPROOM_INVITE_LIFETIME: int = 86400               # сколько живёт приглашение (секунд)
TEMPROOM_THREAD_CATEGORY: int | None = None         # если хотим тексты/ветки в другом разделе

# Список ролей (для панели) 
GENDER_ROLES = [
    {"emoji": "♂️", "id": 1125344221960872004, "name": "♂️"},
    {"emoji": "♀️", "id": 1125344221960872003, "name": "♀️"},
    {"emoji": "❔", "id": 1125344221960872002, "name": "❔"}
]
COLOR_ROLES = [
    {"color": 16711680, "emoji": "❤️", "id": 1338100752299851776, "name": "❤️"},
    {"color": 16738740, "emoji": "🩷", "id": 1338100761141444661, "name": "🩷"},
    {"color": 16753920, "emoji": "🧡", "id": 1338100760088412210, "name": "🧡"},
    {"color": 16776960, "emoji": "💛", "id": 1338100753167945841, "name": "💛"},
    {"color": 65280, "emoji": "💚", "id": 1338100753751080992, "name": "💚"},
    {"color": 255, "emoji": "💙", "id": 1338100755311231046, "name": "💙"},
    {"color": 65535, "emoji": "🩵", "id": 1338100759178514453, "name": "🩵"},
    {"color": 8388736, "emoji": "💜", "id": 1338100758205169686, "name": "💜"},
    {"color": 10824234, "emoji": "🤎", "id": 1338106700321919036, "name": "🤎"},
    {"color": 1, "emoji": "🖤", "id": 1338100757404319824, "name": "🖤"},
    {"color": 8421504, "emoji": "🩶", "id": 1338100762273775726, "name": "🩶"},
    {"color": 16777215, "emoji": "🤍", "id": 1338100756028592233, "name": "🤍"}
]
OPTIONAL_ROLES = [
    {"id": 1364498609340416040, "name": "Новости", "description": "Уведомления о новостях", "emoji": "📰"},
    {"id": 1364498617758388245, "name": "Розыгрыши", "description": "Уведомления о розыгрышах", "emoji": "🎁"}
]