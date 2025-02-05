from typing import Dict, List, Union
import discord
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

    # --- STATUS ---
    DOT = '<:BotDot:1266063532517232701>'
    ERROR = "<:BotStatusError:1334479369833287682>"
    WARNING = "<:BotStatusWarning:1334479450951122954>"
    SUCCESS = "<:BotStatusSuccess:1334479519612010537>"
    INFO = "<:BotStatusInfo:1334479584447696936>"
    # --- ECONOMY ---
    MONEY = "<:BotInfoMoney:1335400643464007710>"
    # --- OTHER ---
    # Эмодзи для других символов
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
    # --- TEMP VOICES ---
    VOICE_OWNER = discord.PartialEmoji(name="BotVoiceOwner", id=1336443766818607125)
    VOICE_ACCESS = discord.PartialEmoji(name="BotVoiceAccess", id=1336444624952360960)
    VOICE_LIMIT = discord.PartialEmoji(name="BotVoiceLimit", id=1336442691466039336)
    VOICE_LOCK = discord.PartialEmoji(name="BotVoiceLock", id=1336445141145223178)
    VOICE_EDIT = discord.PartialEmoji(name="BotVoiceEdit", id=1336440917179236516)
    VOICE_TRUST = discord.PartialEmoji(name="BotVoiceTrust", id=1336448274718130176)
    VOICE_UNTRUST = discord.PartialEmoji(name="BotVoiceUntrust", id=1336448623189168159)
    VOICE_INVITE = discord.PartialEmoji(name="BotVoiceInvite", id=1336450141019836547)
    VOICE_BAN = discord.PartialEmoji(name="BotVoiceBan", id=1336451916414058536)
    VOICE_UNBAN = discord.PartialEmoji(name="BotVoiceUnban", id=1336452202453012583)
    VOICE_REVOKE = discord.PartialEmoji(name="BotVoiceRevoke", id=1336453162588049418)
    VOICE_THREAD = discord.PartialEmoji(name="BotVoiceThread", id=1336453454180122624)
    VOICE_REGION = discord.PartialEmoji(name="BotVoiceRegion", id=1336453956796284979)
    VOICE_DELETE = discord.PartialEmoji(name="BotVoiceDelete", id=1336454612999340225)
    # --- ANALYTICS ---
    STATS = '<:AnalyticsStats:1332731704015847455>'
    INFO = '<:AnalyticsInfo:1332731894491779164>'
    MEMBERS = '<:AnalyticsMembers:1332732020991721502>'
    BOOST = '<:AnalyticsBoost:1332732537956466698>'
    SHIELD = '<:AnalyticsSecurity:1332732698611023882>'
    FEATURES = '<:AnalyticsFeature:1332732366812221440>'
    CHANNELS = '<:AnalyticsChannels:1332732203242750092>'
    SETTINGS = '<:AnalyticsSettings:1332732862004461638>'
    OTHER = '<:AnalyticsOther:1332731704015847455>'
    PC = '<:AnalyticsPC:1332733064375177288>'
    LINK = '<:AnalyticsLink:1332733206956474478>'
    ROLES = '<:AnalyticsRoles:1332733459893846089>'
    CROWN = '<:AnalyticsCrown:1332733632896303186>'
    BOT = '<:AnalyticsBot:1332734596449697823>'
    # --- STREAK INFO ---
    CALENDAR = '<:BotCalendar:1332836632449257525>'
    MESSAGE = '<:BotMessages:1332836789383073893>'
    STATUS = '<:BotStatus:1332837240929255464>'
    CLOCK = '<:BotClock:1332837421603360799>'
    # --- 2048 ---
    TILE_0 = '⬛'
    TILE_2 = '<:2048_2:1333180133258956882>'
    TILE_4 = '<:2048_4:1333180162950565979>'
    TILE_8 = '<:2048_8:1333180190855270400>'
    TILE_16 = '<:2048_16:1333180223763775662>'
    TILE_32 = '<:2048_32:1333180256516837376>'
    TILE_64 = '<:2048_64:1333180298145435719>'
    TILE_128 = '<:2048_128:1333180326436016208>'
    TILE_256 = '<:2048_256:1333180358891409440>'
    TILE_512 = '<:2048_512:1333180385277902858>'
    TILE_1024 = '<:2048_1024:1333180415619629179>'
    TILE_2048 = '<:2048_2048:1333180450402996378>'
    # --- LEVELS ---
    LEVEL = '🎯'
    XP = '✨'
    LEVELUP = '🎉'
    RANK = '🏆'
    LEADERBOARD = '📊'
    REPUTATION = '⭐'
    UP = '⬆️'
    DOWN = '⬇️'
    CASH = '💵'
    BANK = '🏦'
    TOTAL = '💰'
    # --- BIO ---
    NAME = '🔍'
    AGE = '🌈'
    COUNTRY = '🌍'
    BIO = '💬'
    PROFILE = '👤'
    # --- MUSIC ---
    MUSIC = '🎧'
    NOW_PLAYING = '🎧'
    PAUSE = '⏸️'
    PLAY = '▶️'
    STOP = '⏹️'
    SKIP = '⏭️'
    NEXT = '⏭️'
    QUEUE = '🎧'
    TIME = '⏰'
    USER = '👤'
    ARTIST = '🎤'
    LIVE = '🔴'
    PLAYLIST = '🎧'
    EFFECT = '🎧'
    REPEAT = '🔁'
    REPEAT_ONE = '🔂'
    SHUFFLE = '🔀'
    REMOVE = '🗑️'
    REMOVE_ALL = '🗑️'
    PAUSE_ALL = '⏸️'
    RESUME_ALL = '▶️'
    STOP_ALL = '⏹️'
    VOLUME = '🔊'
    VOLUME_DOWN = '🔉'
    VOLUME_UP = '🔈'
    MUTE = '🔇'
    UNMUTE = '🔈'
    VOLUME_LOW = '🔈'
    VOLUME_MEDIUM = '🔉'
    VOLUME_HIGH = '🔊'
    VOLUME_MUTE = '🔇'
    KARAOKE = '🎤'
    # --- BAN ---
    UNBAN = '🔓'
    BAN = '🔒'
    MUTE = '🔇'
    UNMUTE = '🔈'
    KICK = '👢'
    BAN_USER = '🔒'
    UNBAN_USER = '🔓'
    SHIELD = '🛡️'
    USER = '👤'
    SERVER = '🏠'
    REASON = '🔍'
    TIME = '⏰'
    LOADING = '🔄'
    CHANNEL = '💬'
    SEARCH = '🔍'
    STATS = '📊'
    WEBHOOK = '🔗'
    INVITE = '🔗'
    MESSAGE = '💬'
    LOCK = '🔒'
    UNLOCK = '🔓'
    ROLE = '🎭'
    SETTINGS = '⚙️'
    # --- AVATAR ---
    AVATAR = '👤'
    DOWNLOAD = '💾'
    PARTNER = '🤝'
    LINK = '🔗'
    VERIFY = '🔑'
    WELCOME = '👋'

