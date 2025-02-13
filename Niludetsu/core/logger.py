"""
Система логирования Niludetsu
"""
import discord
from typing import Union, Optional, Dict, Any, List
from datetime import datetime
import asyncio

from ..database.db import Database
from ..utils.embed import Embed

class LoggingState:
    """Глобальное состояние системы логирования"""
    webhook: Optional[discord.Webhook] = None
    log_channel: Optional[discord.TextChannel] = None
    initialized: bool = False
    last_message_time: Optional[datetime] = None
    initialized_loggers: List[str] = []
    rate_limit_delay: float = 1.0
    initialization_in_progress: bool = False

    @classmethod
    def initialize(cls, channel: discord.TextChannel) -> None:
        """Инициализация состояния логирования"""
        if cls.initialized and cls.log_channel and cls.log_channel.id == channel.id:
            return
        cls.log_channel = channel
        cls.initialized = True

class BaseLogger:
    """Базовый класс для всех логгеров"""
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.owner_id = "636570363605680139"
        if not LoggingState.initialized and not LoggingState.initialization_in_progress:
            LoggingState.initialization_in_progress = True
            bot.loop.create_task(self.initialize_logs())

    async def initialize_logs(self) -> None:
        """Инициализация логирования"""
        try:
            if LoggingState.initialized:
                return

            if not self.bot.is_ready():
                await self.bot.wait_until_ready()

            result = await self.db.fetch_one(
                "SELECT value FROM settings WHERE category = 'logging' AND key = 'main_channel'"
            )
            
            if not result:
                print("❌ Канал для логов не настроен в базе данных")
                try:
                    owner = await self.bot.fetch_user(int(self.owner_id))
                    if owner:
                        await owner.send("❌ Канал для логов не настроен в базе данных. Используйте команду для настройки логов.")
                except:
                    pass
                return
                
            try:
                channel_id = int(result['value'])
                channel = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(channel_id)
                
                if not isinstance(channel, discord.TextChannel):
                    print(f"❌ Канал с ID {channel_id} не является текстовым каналом на сервере")
                    return

                permissions = channel.permissions_for(channel.guild.me)
                if not permissions.send_messages or not permissions.manage_webhooks:
                    print(f"❌ Недостаточно прав в канале логов {channel_id}")
                    return
                
                LoggingState.initialize(channel)
                
                webhooks = await channel.webhooks()
                bot_webhooks = [w for w in webhooks if w.user and w.user.id == self.bot.user.id]
                
                if bot_webhooks:
                    LoggingState.webhook = bot_webhooks[0]
                    for webhook in bot_webhooks[1:]:
                        await webhook.delete()
                else:
                    LoggingState.webhook = await channel.create_webhook(name=f"{self.bot.user.name} Logger")

                logger_name = self.__class__.__name__.replace('Logger', '')
                if logger_name not in LoggingState.initialized_loggers:
                    LoggingState.initialized_loggers.append(logger_name)

            except discord.NotFound:
                print(f"❌ Канал с ID {channel_id} не найден")
            except discord.Forbidden:
                print(f"❌ Нет доступа к каналу с ID {channel_id}")
            except Exception as e:
                print(f"❌ Ошибка при настройке канала логов: {e}")
                
        except Exception as e:
            print(f"❌ Ошибка при инициализации логов: {e}")
        finally:
            LoggingState.initialization_in_progress = False

    async def log_event(self, title: str, description: str = "", color: Union[str, int] = 'BLUE', 
                       fields: Optional[List[Dict[str, Any]]] = None, event_type: str = "general", **kwargs) -> None:
        """Базовый метод для логирования событий"""
        try:
            if not LoggingState.initialized or not LoggingState.log_channel:
                return
            
            timestamp = kwargs.pop('timestamp', discord.utils.utcnow())
            embed = Embed(
                title=title,
                description=description,
                color=color,
                fields=fields,
                timestamp=timestamp,
                **kwargs
            )

            current_time = datetime.utcnow()
            if LoggingState.last_message_time:
                time_diff = (current_time - LoggingState.last_message_time).total_seconds()
                if time_diff < LoggingState.rate_limit_delay:
                    await asyncio.sleep(LoggingState.rate_limit_delay - time_diff)
            
            try:
                if LoggingState.webhook:
                    await LoggingState.webhook.send(embed=embed)
                else:
                    await LoggingState.log_channel.send(embed=embed)
                
                LoggingState.last_message_time = datetime.utcnow()
                
            except discord.Forbidden:
                print("❌ Нет прав для отправки сообщений в канал логов")
            except discord.HTTPException as e:
                print(f"❌ Ошибка Discord API при отправке лога: {e}")
            
        except Exception as e:
            print(f"❌ Ошибка при логировании события: {e}")

    @staticmethod
    def format_diff(before: Any, after: Any) -> str:
        """Форматирует разницу между значениями для отображения в логах"""
        if isinstance(before, bool) or isinstance(after, bool):
            return f"`{before}` → `{after}`"
        elif isinstance(before, (int, float)) or isinstance(after, (int, float)):
            return f"`{before}` → `{after}`"
        elif isinstance(before, str) or isinstance(after, str):
            return f"```{before}``` → ```{after}```"
        else:
            return f"{before} → {after}" 