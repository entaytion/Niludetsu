import discord
from typing import Union, Optional, Dict, Any, List
from datetime import datetime
import yaml
import asyncio
from .decorators import load_config
from ..utils.config_loader import bot_state
from ..utils.embed import Embed

class LoggingState:
    """Глобальное состояние системы логирования"""
    webhook: Optional[discord.Webhook] = None
    log_channel: Optional[discord.TextChannel] = None
    initialized: bool = False
    last_message_time: Optional[datetime] = None
    initialized_loggers: List[str] = []
    rate_limit_delay: float = 1.0

    @classmethod
    def initialize(cls, channel: discord.TextChannel) -> None:
        """Инициализация состояния логирования"""
        if cls.initialized and cls.log_channel and cls.log_channel.id == channel.id:
            return
        cls.log_channel = channel
        cls.initialized = True

class BaseLogger:
    """Базовый класс для всех логгеров"""
    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.owner_id = "636570363605680139"
        if not LoggingState.initialized:
            bot.loop.create_task(self.initialize_logs())

    async def initialize_logs(self) -> None:
        """Инициализация канала логов"""
        if LoggingState.initialized:
            return
            
        await self.bot.wait_until_ready()
        try:
            config = load_config()
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
            webhook = await self.get_webhook(channel)
            if webhook:
                LoggingState.webhook = webhook

        except Exception as e:
            print(f"Ошибка при инициализации логов: {e}")

    async def get_webhook(self, channel: discord.TextChannel) -> Optional[discord.Webhook]:
        """Получение или создание вебхука для логирования"""
        try:
            webhooks = await channel.webhooks()
            webhook = discord.utils.get(webhooks, name='NiluBot Logs')
            
            if not webhook:
                webhook = await channel.create_webhook(name='NiluBot Logs')
            
            return webhook
        except Exception:
            return None

    async def log_event(self, title: str, description: str = "", color: Union[str, int] = 'BLUE', 
                       fields: Optional[List[Dict[str, Any]]] = None, event_type: str = "general", **kwargs) -> None:
        """Базовый метод для логирования событий"""
        try:
            if not LoggingState.initialized or not LoggingState.log_channel:
                return

            # Извлекаем timestamp из kwargs если он есть, иначе используем текущее время
            timestamp = kwargs.pop('timestamp', discord.utils.utcnow())

            embed=Embed(
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
            
            if LoggingState.webhook:
                await LoggingState.webhook.send(embed=embed)
            else:
                await LoggingState.log_channel.send(embed=embed)
                
            LoggingState.last_message_time = datetime.utcnow()
            
        except Exception as e:
            print(f"Ошибка при логировании события: {e}")

class Logger(BaseLogger):
    """Класс для работы с логированием"""
    _instance = None
    
    def __new__(cls, bot: discord.Client):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance.__init__(bot)  # Вызываем инициализацию BaseLogger
        return cls._instance

    async def initialize_logs(self) -> None:
        """Инициализация канала логов"""
        if LoggingState.initialized:
            return
            
        await super().initialize_logs()  # Вызываем метод базового класса
        
        # Отправляем только одно сообщение при первой инициализации
        if not bot_state.is_initialized('logging_system'):
            logger_name = self.__class__.__name__.replace('Logger', '')
            if logger_name not in LoggingState.initialized_loggers:
                LoggingState.initialized_loggers.append(logger_name)
                
            if len(LoggingState.initialized_loggers) == 15:  # Общее количество логгеров
                embed=Embed(
                    title="✅ Система логирования активирована",
                    description="Инициализированы следующие логгеры:\n" + 
                              "\n".join([f"• {name}" for name in LoggingState.initialized_loggers]),
                    color='GREEN'
                )
                if LoggingState.webhook:
                    await LoggingState.webhook.send(embed=embed)
                else:
                    await LoggingState.log_channel.send(embed=embed)
                bot_state.mark_initialized('logging_system')

    async def show_logs_info(self, interaction: discord.Interaction) -> None:
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

    async def log_permission_update(self, channel: discord.abc.GuildChannel, 
                                  target: Union[discord.Role, discord.Member], 
                                  before: discord.PermissionOverwrite, 
                                  after: discord.PermissionOverwrite) -> None:
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

    async def log_role_update(self, role: discord.Role, before: discord.Role, after: discord.Role) -> None:
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

    async def log_channel_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel) -> None:
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

    @staticmethod
    def format_diff(before: Any, after: Any) -> str:
        """Форматирование разницы между значениями для логов"""
        return f"До: {before}\nПосле: {after}" 