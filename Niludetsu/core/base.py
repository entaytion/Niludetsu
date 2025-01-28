import discord
from discord.ext import commands
import aiohttp
import yaml
import traceback
from typing import Optional, Dict, Any, Union, List
from discord import app_commands, Embed, Colour
from ..utils.config_loader import bot_state
from datetime import datetime
import asyncio

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
    'DEFAULT': 0xf20c3c,
    'GREEN': 0x30f20c,
    'YELLOW': 0xf1f20c,
    'RED': 0xf20c3c,
    'BLUE': 0x0c3ef2,
    'WHITE': 0xFFFFFF,
    'BLACK': 0x000000
}

# --- EMBED STRUCTURE ---
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

class LoggingState:
    """Глобальное состояние системы логирования"""
    webhook: Optional[discord.Webhook] = None
    log_channel: Optional[discord.TextChannel] = None
    initialized: bool = False
    last_message_time: Optional[datetime] = None
    initialized_loggers: List[str] = []
    rate_limit_delay: float = 1.0  # Уменьшаем задержку между сообщениями
    
    @classmethod
    def initialize(cls, channel: discord.TextChannel):
        if cls.initialized and cls.log_channel and cls.log_channel.id == channel.id:
            return
        cls.log_channel = channel
        cls.initialized = True

class BaseLogger:
    """Базовый класс для всех логгеров."""
    _instance = None
    
    def __new__(cls, bot: commands.Bot):
        if cls._instance is None:
            cls._instance = super(BaseLogger, cls).__new__(cls)
            cls._instance.bot = bot
            cls._instance.owner_id = "636570363605680139"
            if not LoggingState.initialized:
                bot.loop.create_task(cls._instance.initialize_logs())
        return cls._instance

    async def initialize_logs(self):
        """Инициализация канала логов"""
        if LoggingState.initialized:
            return
            
        await self.bot.wait_until_ready()
        try:
            with open('config/config.yaml', 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                if 'logging' not in config or 'main_channel' not in config['logging']:
                    return
                    
                channel_id = int(config['logging']['main_channel'])
                channel = self.bot.get_channel(channel_id)
                
                if not channel:
                    try:
                        channel = await self.bot.fetch_channel(channel_id)
                    except Exception:
                        return
                
                LoggingState.initialize(channel)
                
                # Получаем или создаем вебхук
                webhook = await self.get_webhook(channel)
                if webhook:
                    LoggingState.webhook = webhook
                
                # Отправляем только одно сообщение при первой инициализации
                if not bot_state.is_initialized('logging_system'):
                    logger_name = self.__class__.__name__.replace('Logger', '')
                    if logger_name not in LoggingState.initialized_loggers:
                        LoggingState.initialized_loggers.append(logger_name)
                        
                    if len(LoggingState.initialized_loggers) == 15:  # Общее количество логгеров
                        embed = discord.Embed(
                            title="✅ Система логирования активирована",
                            description="Инициализированы следующие логгеры:\n" + 
                                      "\n".join([f"• {name}" for name in LoggingState.initialized_loggers]),
                            color=discord.Color.green()
                        )
                        if LoggingState.webhook:
                            await LoggingState.webhook.send(embed=embed)
                        else:
                            await channel.send(embed=embed)
                        bot_state.mark_initialized('logging_system')
                
        except Exception as e:
            print(f"Ошибка при инициализации логов: {e}")

    async def get_webhook(self, channel: discord.TextChannel) -> Optional[discord.Webhook]:
        """Получение или создание вебхука"""
        try:
            webhooks = await channel.webhooks()
            webhook = discord.utils.get(webhooks, name='NiluBot Logs')
            
            if not webhook:
                webhook = await channel.create_webhook(name='NiluBot Logs')
            
            return webhook
        except Exception:
            return None

    async def log_event(self, title: str, description: str = "", color: Union[str, int] = 'BLUE', 
                       fields: Optional[List[Dict[str, Any]]] = None, event_type: str = "general", **kwargs):
        """Логирование события"""
        try:
            if not LoggingState.initialized or not LoggingState.log_channel:
                return
                
            # Создаем эмбед
            if isinstance(color, str):
                color = COLORS.get(color.upper(), COLORS['DEFAULT'])
            
            embed = create_embed(
                title=title,
                description=description,
                color=color,
                fields=fields,
                timestamp=discord.utils.utcnow(),
                **kwargs
            )
            
            # Отправляем сообщение с учетом задержки
            current_time = datetime.utcnow()
            if LoggingState.last_message_time:
                time_diff = (current_time - LoggingState.last_message_time).total_seconds()
                if time_diff < LoggingState.rate_limit_delay:
                    await asyncio.sleep(LoggingState.rate_limit_delay - time_diff)
            
            if LoggingState.webhook:
                await LoggingState.webhook.send(embed=embed)
            else:
                await LoggingState.log_channel.send(embed=embed)
                
            LoggingState.last_message_time = datetime.utcnow()
            
        except Exception as e:
            print(f"Ошибка при логировании события: {e}")

    @staticmethod
    def format_diff(before: Any, after: Any) -> str:
        """Форматирование разницы между значениями для логов."""
        return f"До: {before}\nПосле: {after}"

    async def show_logs_info(self, interaction: discord.Interaction):
        """Показывает информацию о текущем канале логов"""
        try:
            if LoggingState.log_channel:
                await self.log_event(
                    title="📝 Информация о логах",
                    description=f"Текущий канал логов: {LoggingState.log_channel.mention}\n"
                              f"ID канала: `{LoggingState.log_channel.id}`",
                    color='BLUE'
                )
            else:
                await self.log_event(
                    title="❌ Канал логов не настроен",
                    description="Проверьте настройки в файле config.yaml",
                    color='RED'
                )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Произошла ошибка: {str(e)}"
            )

    async def log_permission_update(self, channel: discord.abc.GuildChannel, target: Union[discord.Role, discord.Member], 
                                  before: discord.PermissionOverwrite, after: discord.PermissionOverwrite):
        """Логирование изменений прав доступа"""
        try:
            changes = []
            for perm, value in after.pair()[0]:
                before_value = getattr(before.pair()[0], perm)
                if before_value != value:
                    changes.append(f"• `{perm}`: {before_value} → {value}")

            if changes:
                target_type = "роли" if isinstance(target, discord.Role) else "пользователя"
                await self.log_event(
                    title=f"🔒 Права {target_type} обновлены",
                    description=f"**Канал:** {channel.mention}\n"
                              f"**{target_type.title()}:** {target.mention}\n"
                              f"**Изменения:**\n" + "\n".join(changes),
                    color='BLUE',
                    event_type="permissions"
                )
        except Exception as e:
            print(f"Ошибка при логировании изменений прав: {e}")

    async def log_role_update(self, role: discord.Role, before: discord.Role, after: discord.Role):
        """Логирование изменений роли"""
        try:
            changes = []
            if before.name != after.name:
                changes.append(f"• Название: `{before.name}` → `{after.name}`")
            if before.color != after.color:
                changes.append(f"• Цвет: `{before.color}` → `{after.color}`")
            if before.hoist != after.hoist:
                changes.append(f"• Отображение отдельно: `{before.hoist}` → `{after.hoist}`")
            if before.mentionable != after.mentionable:
                changes.append(f"• Упоминание: `{before.mentionable}` → `{after.mentionable}`")
            if before.permissions != after.permissions:
                perm_changes = []
                for perm, value in after.permissions:
                    if getattr(before.permissions, perm) != value:
                        perm_changes.append(f"`{perm}`: {getattr(before.permissions, perm)} → {value}")
                if perm_changes:
                    changes.append("• Права:\n" + "\n".join(perm_changes))

            if changes:
                await self.log_event(
                    title="👥 Роль изменена",
                    description=f"**Роль:** {after.mention}\n"
                              f"**ID:** `{after.id}`\n"
                              f"**Изменения:**\n" + "\n".join(changes),
                    color='BLUE',
                    event_type="roles"
                )
        except Exception as e:
            print(f"Ошибка при логировании изменений роли: {e}")

    async def log_channel_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        """Логирование изменений канала"""
        try:
            changes = []
            if before.name != after.name:
                changes.append(f"• Название: `{before.name}` → `{after.name}`")
            if isinstance(before, discord.TextChannel) and isinstance(after, discord.TextChannel):
                if before.topic != after.topic:
                    changes.append(f"• Описание: `{before.topic}` → `{after.topic}`")
                if before.slowmode_delay != after.slowmode_delay:
                    changes.append(f"• Медленный режим: `{before.slowmode_delay}с` → `{after.slowmode_delay}с`")
            if isinstance(before, discord.VoiceChannel) and isinstance(after, discord.VoiceChannel):
                if before.bitrate != after.bitrate:
                    changes.append(f"• Битрейт: `{before.bitrate//1000}kbps` → `{after.bitrate//1000}kbps`")
                if before.user_limit != after.user_limit:
                    changes.append(f"• Лимит пользователей: `{before.user_limit}` → `{after.user_limit}`")
            if before.category != after.category:
                before_category = before.category.name if before.category else "Нет"
                after_category = after.category.name if after.category else "Нет"
                changes.append(f"• Категория: `{before_category}` → `{after_category}`")
            if before.position != after.position:
                changes.append(f"• Позиция: `{before.position}` → `{after.position}`")

            if changes:
                channel_type = "Текстовый канал" if isinstance(after, discord.TextChannel) else "Голосовой канал"
                await self.log_event(
                    title=f"📝 {channel_type} изменен",
                    description=f"**Канал:** {after.mention}\n"
                              f"**ID:** `{after.id}`\n"
                              f"**Изменения:**\n" + "\n".join(changes),
                    color='BLUE',
                    event_type="channels"
                )
        except Exception as e:
            print(f"Ошибка при логировании изменений канала: {e}") 