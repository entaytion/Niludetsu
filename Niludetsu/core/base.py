import discord
from discord.ext import commands
import aiohttp
import yaml
import traceback
from typing import Optional, Dict, Any, Union
from discord import app_commands, Embed, Colour

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

# --- BASE LOGGER ---
class BaseLogger:
    """Базовый класс для всех логгеров."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.owner_id = "636570363605680139"
        self.log_channel: Optional[discord.TextChannel] = None
        self.webhook_url: Optional[str] = None
        self.webhook: Optional[discord.Webhook] = None
        bot.loop.create_task(self.initialize_logs())
        
    async def initialize_logs(self):
        """Инициализация канала логов"""
        await self.bot.wait_until_ready()
        try:
            with open('config/config.yaml', 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                if 'logging' in config and 'main_channel' in config['logging']:
                    channel_id = int(config['logging']['main_channel'])
                    self.log_channel = self.bot.get_channel(channel_id)
                    
                    if not self.log_channel:
                        print(f"❌ Канал логов не найден! ID: {channel_id}")
                        try:
                            self.log_channel = await self.bot.fetch_channel(channel_id)
                            print(f"✅ Канал логов успешно получен через fetch: {self.log_channel.name}")
                        except Exception as e:
                            print(f"❌ Не удалось получить канал через fetch: {e}")
                            return
                            
                    print(f"✅ Канал логов успешно установлен: {self.log_channel.name}")
                    
                    # Инициализация вебхука
                    webhook = await self.get_webhook(self.log_channel)
                    if webhook:
                        self.webhook = webhook
                        self.webhook_url = webhook.url
                        print("✅ Система логирования активирована")
                    
        except Exception as e:
            print(f"❌ Ошибка при инициализации логов: {e}")
            print(traceback.format_exc())
            
    def save_config(self, channel_id: int):
        """Сохранение конфигурации"""
        try:
            with open('config/config.yaml', 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            config['logging']['main_channel'] = str(channel_id)
            
            with open('config/config.yaml', 'w', encoding='utf-8') as f:
                yaml.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")
            
    async def get_webhook(self, channel: discord.TextChannel) -> Optional[discord.Webhook]:
        """Получение или создание вебхука"""
        try:
            webhooks = await channel.webhooks()
            webhook = discord.utils.get(webhooks, name='NiluBot Logs')
            
            if not webhook:
                webhook = await channel.create_webhook(name='NiluBot Logs')
            
            return webhook
        except discord.Forbidden:
            print(f"❌ Нет прав для управления вебхуками в канале {channel.name}")
            return None
        except Exception as e:
            print(f"❌ Ошибка при работе с вебхуком: {e}")
            return None
            
    async def log_event(self, title: str, description: str, color='DEFAULT', fields=None, footer=None, image_url=None, author=None, url=None, timestamp=None, thumbnail_url=None, file: discord.File = None) -> None:
        """Отправка сообщения в лог-канал"""
        if not self.log_channel:
            return

        try:
            embed = create_embed(
                title=title,
                description=description,
                color=color,
                fields=fields,
                footer=footer,
                image_url=image_url,
                author=author,
                url=url,
                timestamp=timestamp,
                thumbnail_url=thumbnail_url
            )

            if self.webhook:
                if file:
                    await self.webhook.send(embed=embed, file=file)
                else:
                    await self.webhook.send(embed=embed)
        except Exception as e:
            print(f"Error in log_event: {str(e)}")
            
    async def log_error(self, error, command_name: str, author_mention: str, author_id: str, channel_mention: str):
        """Общий метод для логирования ошибок команд"""
        if self.log_channel:
            error_trace = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
            await self.log_channel.send(f"<@{self.owner_id}>, произошла ошибка!")
            
            fields = [
                {"name": f"{EMOJIS['DOT']} Команда", "value": f"`{command_name}`", "inline": True},
                {"name": f"{EMOJIS['DOT']} Автор", "value": f"{author_mention} (`{author_id}`)", "inline": True},
                {"name": f"{EMOJIS['DOT']} Канал", "value": channel_mention, "inline": True},
                {"name": f"{EMOJIS['DOT']} Ошибка", "value": f"```py\n{error_trace[:1900]}```", "inline": False}
            ]
            
            await self.log_event(
                title="⚠️ Ошибка команды",
                description="",
                color='RED',
                fields=fields,
                author={'name': 'Command Error'}
            )

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Логирование ошибок команд"""
        if self.log_channel:
            if isinstance(ctx, discord.Interaction):
                command_name = f"/{ctx.command.parent.name if ctx.command.parent else ''}{' ' if ctx.command.parent else ''}{ctx.command.name}"
                author = ctx.user
            else:
                command_name = ctx.message.content
                author = ctx.author
                
            await self.log_error(
                error=error,
                command_name=command_name,
                author_mention=author.mention,
                author_id=str(author.id),
                channel_mention=ctx.channel.mention
            )

    @commands.Cog.listener()
    async def on_app_command_error(self, interaction: discord.Interaction, error):
        """Перенаправление ошибок slash-команд в основной обработчик"""
        await self.on_command_error(interaction, error)
        
    @staticmethod
    def format_diff(before: Any, after: Any) -> str:
        """Форматирование разницы между значениями для логов."""
        return f"До: {before}\nПосле: {after}"
        
    async def show_logs_info(self, interaction: discord.Interaction):
        """Показывает информацию о текущем канале логов"""
        try:
            if self.log_channel:
                await self.log_event(
                    title="📝 Информация о логах",
                    description=f"Текущий канал логов: {self.log_channel.mention}\n"
                              f"ID канала: `{self.log_channel.id}`",
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