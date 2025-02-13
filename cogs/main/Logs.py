"""
Команды для управления системой логирования
"""
import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import asyncio
import inspect

from Niludetsu import (
    Embed,
    Emojis,
    admin_only,
    Database,
    Tables,
    ChannelLogger,
    EmojiLogger,
    ErrorLogger,
    EventLogger,
    InviteLogger,
    MessageLogger,
    PollLogger,
    RoleLogger,
    ServerLogger,
    SoundboardLogger,
    StageLogger,
    StickerLogger,
    ThreadLogger,
    UserLogger,
    VoiceLogger,
    WebhookLogger,
    AutoModLogger,
    ApplicationLogger,
    EntitlementLogger,
    LoggingState
)

class Logs(commands.Cog):
    LOGGER_CLASSES = {
        'channels': ChannelLogger,
        'emojis': EmojiLogger,
        'errors': ErrorLogger,
        'events': EventLogger,
        'invites': InviteLogger,
        'messages': MessageLogger,
        'polls': PollLogger,
        'roles': RoleLogger,
        'server': ServerLogger,
        'soundboards': SoundboardLogger,
        'stage': StageLogger,
        'stickers': StickerLogger,
        'threads': ThreadLogger,
        'users': UserLogger,
        'voice': VoiceLogger,
        'webhooks': WebhookLogger,
        'automod': AutoModLogger,
        'applications': ApplicationLogger,
        'entitlements': EntitlementLogger
    }

    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.loggers = {}
        self._event_handlers = {}
        asyncio.create_task(self._initialize())

    def _create_event_handler(self, event_name: str):
        """Создает обработчик события для всех логгеров"""
        async def handler(*args, **kwargs):
            if not LoggingState.initialized or not self.loggers:
                print(f"❌ Логирование не инициализировано для {event_name}")
                return

            try:
                print(f"🔄 Обработка события {event_name}")
                print(f"📝 Аргументы события: {args}")
                
                # Пропускаем сообщения от ботов
                if event_name.startswith('on_message') and hasattr(args[0], 'author'):
                    if args[0].author.bot:
                        print(f"❌ Пропуск сообщения бота в {event_name}")
                        return
                elif event_name.startswith('on_message_edit') and hasattr(args[0], 'author'):
                    if args[0].author.bot:
                        print(f"❌ Пропуск редактирования сообщения бота в {event_name}")
                        return

                # Проверяем, что событие произошло на сервере
                guild_id = None
                if len(args) > 0:
                    if hasattr(args[0], 'guild') and args[0].guild:
                        guild_id = args[0].guild.id
                    elif hasattr(args[0], 'guild_id'):
                        guild_id = args[0].guild_id
                    # Проверяем второй аргумент для событий типа voice_state_update
                    elif len(args) > 1 and hasattr(args[1], 'guild'):
                        guild_id = args[1].guild.id
                
                if not guild_id:
                    print(f"❌ Не найден guild_id для {event_name}")
                    return

                # Получаем имя метода логирования из имени события
                log_method_name = f"log_{event_name[3:]}"
                print(f"🔍 Ищем метод {log_method_name}")

                # Проходим по всем логгерам
                for logger_name, logger in self.loggers.items():
                    try:
                        if hasattr(logger, log_method_name):
                            print(f"✅ Найден метод {log_method_name} в логгере {logger_name}")
                            log_method = getattr(logger, log_method_name)
                            
                            # Проверяем количество параметров метода
                            params = inspect.signature(log_method).parameters
                            print(f"📊 Метод {log_method_name} ожидает {len(params)} параметров, получено {len(args)}")
                            
                            # Проверяем соответствие параметров
                            if len(params) == len(args):
                                print(f"🚀 Вызываем {log_method.__name__} с {len(args)} аргументами")
                                await log_method(*args)
                            else:
                                print(f"❌ Несоответствие параметров для {log_method_name}: ожидается {len(params)}, получено {len(args)}")
                                print(f"📝 Параметры метода: {list(params.keys())}")
                                print(f"📝 Полученные аргументы: {args}")
                    except Exception as e:
                        print(f"❌ Ошибка в логгере {logger_name} при обработке {event_name}: {e}")
                        import traceback
                        print(f"Traceback: {traceback.format_exc()}")

            except Exception as e:
                print(f"❌ Общая ошибка при обработке {event_name}: {e}")
                import traceback
                print(f"Traceback: {traceback.format_exc()}")

        return handler

    async def _initialize(self):
        """Асинхронная инициализация"""
        try:
            await self.bot.wait_until_ready()
            await self.db.init()
            
            print("🔄 Инициализация системы логирования...")
            
            # Загружаем канал логов из базы данных
            result = await self.db.fetch_one(
                "SELECT value FROM settings WHERE category = 'logging' AND key = 'main_channel'"
            )
            
            if not result:
                print("❌ Канал для логов не настроен в базе данных")
                return
                
            channel_id = int(result['value'])
            channel = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(channel_id)
            
            if not isinstance(channel, discord.TextChannel):
                print(f"❌ Канал {channel_id} не является текстовым")
                return
                
            # Проверяем права
            permissions = channel.permissions_for(channel.guild.me)
            if not permissions.send_messages or not permissions.manage_webhooks:
                print(f"❌ Недостаточно прав в канале логов {channel_id}")
                return
                
            # Инициализируем состояние логирования
            LoggingState.initialize(channel)
            
            # Создаем или получаем вебхук
            webhooks = await channel.webhooks()
            bot_webhook = discord.utils.get(webhooks, user=self.bot.user)
            
            if not bot_webhook:
                try:
                    LoggingState.webhook = await channel.create_webhook(name=f"{self.bot.user.name} Logger")
                    print("✅ Создан новый вебхук для логов")
                except discord.Forbidden:
                    print("❌ Не удалось создать вебхук для логов")
                    return
            else:
                LoggingState.webhook = bot_webhook
                print("✅ Найден существующий вебхук для логов")

            # Инициализируем логгеры
            print("\n🔄 Инициализация логгеров...")
            for name, logger_class in self.LOGGER_CLASSES.items():
                self.loggers[name] = logger_class(self.bot)
                print(f"✅ Загружен логгер: {name}")

            # Автоматически регистрируем обработчики событий
            print("\n🔄 Регистрация обработчиков событий...")
            registered_events = []
            for logger in self.loggers.values():
                for method_name in dir(logger):
                    if method_name.startswith('log_'):
                        event_name = f"on_{method_name[4:]}"
                        if event_name not in self._event_handlers:
                            handler = self._create_event_handler(event_name)
                            self._event_handlers[event_name] = handler
                            self.bot.add_listener(handler, event_name)
                            registered_events.append(event_name)
            
            if registered_events:
                print(f"\n✅ Всего зарегистрировано {len(registered_events)} обработчиков.")
            else:
                print("\n❌ Не найдено методов для регистрации обработчиков!")
            
            print(f"\n✅ Система логирования инициализирована в канале {channel.name}")
            
            # Отправляем тестовое сообщение
            try:
                test_embed = Embed(
                    title=f"{Emojis.SUCCESS} Система логирования активна",
                    description="Канал успешно настроен для логирования событий.",
                    color="GREEN"
                )
                if LoggingState.webhook:
                    await LoggingState.webhook.send(embed=test_embed)
                else:
                    await channel.send(embed=test_embed)
                print("✅ Отправлено тестовое сообщение")
            except Exception as e:
                print(f"❌ Ошибка при отправке тестового сообщения: {e}")
                
        except Exception as e:
            print(f"❌ Ошибка при инициализации логов: {e}")

    @app_commands.command(name="logs", description="Настройка системы логирования")
    @app_commands.describe(
        channel="Канал для отправки логов",
        category="Категория логов для настройки"
    )
    @admin_only()
    async def logs(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        category: Optional[str] = None
    ):
        """Настройка системы логирования"""
        try:
            # Проверяем права бота в канале
            permissions = channel.permissions_for(interaction.guild.me)
            if not permissions.send_messages or not permissions.embed_links or not permissions.manage_webhooks:
                return await interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.ERROR} Ошибка",
                        description="У меня нет необходимых прав в этом канале!\nТребуются права: Отправка сообщений, Встраивание ссылок, Управление вебхуками",
                        color="RED"
                    ),
                    ephemeral=True
                )

            # Сохраняем настройки в базу данных
            await self.db.insert(
                'settings',
                {
                    'guild_id': str(interaction.guild_id),
                    'category': 'logging',
                    'key': 'main_channel',
                    'value': str(channel.id)
                }
            )
            
            if category:
                if category not in self.loggers:
                    return await interaction.response.send_message(
                        embed=Embed(
                            title=f"{Emojis.ERROR} Ошибка",
                            description=f"Неизвестная категория логов: `{category}`\nДоступные категории: {', '.join(f'`{c}`' for c in self.loggers.keys())}",
                            color="RED"
                        ),
                        ephemeral=True
                    )
                    
                await self.db.insert(
                    'settings',
                    {
                        'guild_id': str(interaction.guild_id),
                        'category': 'logging',
                        'key': f'channel_{category}',
                        'value': str(channel.id)
                    }
                )

            # Создаем вебхук для логов если его нет
            webhooks = await channel.webhooks()
            bot_webhook = discord.utils.get(webhooks, user=self.bot.user)
            
            if not bot_webhook:
                try:
                    await channel.create_webhook(name=f"{self.bot.user.name} Logger")
                except discord.Forbidden:
                    return await interaction.response.send_message(
                        embed=Embed(
                            title=f"{Emojis.ERROR} Ошибка",
                            description="Не удалось создать вебхук для логов. Проверьте права бота.",
                            color="RED"
                        ),
                        ephemeral=True
                    )

            success_embed = Embed(
                title=f"{Emojis.SETTINGS} Настройка логов",
                color="GREEN"
            )
            
            if category:
                success_embed.description = f"Канал для логов категории `{category}` установлен: {channel.mention}"
            else:
                success_embed.description = f"Основной канал для логов установлен: {channel.mention}"
                
            await interaction.response.send_message(embed=success_embed)
            
            # Отправляем тестовое сообщение в канал логов
            test_embed = Embed(
                title=f"{Emojis.SUCCESS} Система логирования активирована",
                description="Этот канал будет использоваться для логирования событий на сервере.",
                color="GREEN"
            )
            await channel.send(embed=test_embed)
            
        except Exception as e:
            print(f"❌ Ошибка при настройке логов: {e}")
            await interaction.response.send_message(
                embed=Embed(
                    title=f"{Emojis.ERROR} Ошибка",
                    description=f"Произошла ошибка при настройке логов: {e}",
                    color="RED"
                ),
                ephemeral=True
            )

async def setup(bot: commands.Bot):
    await bot.add_cog(Logs(bot)) 