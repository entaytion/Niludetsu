import discord
from discord.ext import commands
from discord.ext import tasks
import datetime
import re
import pytz
from typing import Optional
from Niludetsu.database.db import Database
from Niludetsu.utils.constants import Emojis
from discord import Embed
import asyncio

class BumpReminder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.check_bumps.start()
        self.timezone = pytz.timezone('Europe/Moscow')
        self.bump_role = None
        self.ready = False
        self.last_number = {}
        # Определяем цвета для эмбедов
        self.colors = {
            'red': discord.Color.red(),
            'green': discord.Color.green(),
            'blue': discord.Color.blue(),
            'yellow': discord.Color.yellow()
        }
        # Определяем имена ботов
        self.bot_names = {
            302050872383242240: "DISBOARD",
            1059103014025171014: "DSGroup",
            464272403766444044: "SD.C Monitoring",
            315926021457051650: "Server Monitoring",
            575776004233232386: "DSMonitoring"
        }
        asyncio.create_task(self._initialize())
        
    async def load_numbers(self):
        """Загрузка последних чисел из базы данных"""
        try:
            # Получаем все записи времени бампов из правильной таблицы
            bump_times = await self.db.fetch_all(
                "SELECT bot_id, next_bump FROM bump_reminders"
            )
            
            print(f"📝 Найдено записей в базе: {len(bump_times)}")
            
            for record in bump_times:
                try:
                    bot_id = int(record['bot_id'])
                    next_bump = datetime.datetime.fromisoformat(record['next_bump'])
                    self.last_number[bot_id] = next_bump
                    print(f"✅ Успешно загружено время для бота {bot_id}: {next_bump}")
                    
                except Exception as e:
                    print(f"❌ Ошибка при обработке записи бампа для бота {record.get('bot_id', 'Unknown')}: {str(e)}")
                    continue
                    
        except Exception as e:
            print(f"❌ Ошибка при загрузке чисел: {e}")
            import traceback
            traceback.print_exc()

    async def _initialize(self):
        """Асинхронная инициализация"""
        try:
            await self.bot.wait_until_ready()  # Ждем пока бот будет готов
            await self.db.init()
            
            # Удаляем старую таблицу и создаем новую с правильной структурой
            await self.db.execute("DROP TABLE IF EXISTS bump_reminders")
            await self.db.execute("""
                CREATE TABLE bump_reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bot_id TEXT UNIQUE NOT NULL,
                    bot_name TEXT NOT NULL,
                    next_bump TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ Таблица bump_reminders успешно создана")
            
            # Загружаем ID роли для пинга
            result = await self.db.fetch_one(
                "SELECT value FROM settings WHERE category = 'bump_reminder' AND key = 'role'"
            )
            if result and result['value']:
                self.bump_role = int(result['value'])
                
            await self.load_numbers()
            self.ready = True
            
        except Exception as e:
            print(f"❌ Ошибка при инициализации: {e}")
            import traceback
            traceback.print_exc()
        
    def cog_unload(self):
        """Остановка задач при выгрузке кога"""
        self.check_bumps.cancel()
        
    def get_current_time(self) -> datetime.datetime:
        """Получение текущего времени с учетом часового пояса"""
        return datetime.datetime.now(self.timezone)
        
    def localize_time(self, dt: datetime.datetime) -> datetime.datetime:
        """Локализация времени в нужный часовой пояс"""
        if dt.tzinfo is None:
            return self.timezone.localize(dt)
        return dt.astimezone(self.timezone)
        
    def parse_discord_timestamp(self, content: str) -> Optional[datetime.datetime]:
        """Парсинг временной метки Discord из сообщения"""
        try:
            # Ищем временную метку в формате <t:timestamp>
            match = re.search(r'<t:(\d+)(?::[RFDTd])?>', content)
            if match:
                timestamp = int(match.group(1))
                return datetime.datetime.fromtimestamp(timestamp, self.timezone)
            return None
        except Exception as e:
            print(f"❌ Ошибка при парсинге временной метки: {e}")
            return None
            
    def extract_time_from_text(self, text: str, bot_id: int) -> Optional[datetime.datetime]:
        """Извлечение времени следующего бампа из текста сообщения"""
        try:
            if not text:
                return None

            # Для Disboard
            if bot_id == 302050872383242240:
                if "Bump done!" in text:
                    return self.get_current_time() + datetime.timedelta(hours=2)

            # Для DSGroup
            elif bot_id == 1059103014025171014:
                # Ищем временную метку в формате <t:timestamp:R>
                timestamp_match = re.search(r'<t:(\d+):[Rf]>', text)
                if timestamp_match:
                    timestamp = int(timestamp_match.group(1))
                    return datetime.datetime.fromtimestamp(timestamp, self.timezone)

            # Для SD.C Monitoring
            elif bot_id == 464272403766444044:
                # Ищем временную метку в формате <t:timestamp:T>
                timestamp_match = re.search(r'<t:(\d+):[RT]>', text)
                if timestamp_match:
                    timestamp = int(timestamp_match.group(1))
                    return datetime.datetime.fromtimestamp(timestamp, self.timezone)

            # Для Server Monitoring
            elif bot_id == 315926021457051650:
                # Ищем время в формате HH:MM:SS
                time_match = re.search(r'available in (\d{2}):(\d{2}):(\d{2})', text)
                if time_match:
                    hours = int(time_match.group(1))
                    minutes = int(time_match.group(2))
                    seconds = int(time_match.group(3))
                    total_seconds = hours * 3600 + minutes * 60 + seconds
                    return self.get_current_time() + datetime.timedelta(seconds=total_seconds)

            # Для DSMonitoring
            elif bot_id == 575776004233232386:
                # Проверяем успешный лайк
                if "Вы успешно лайкнули сервер" in text or "Следующий лайк" in text:
                    # Ищем время в формате "Сегодня, в HH:MM"
                    time_match = re.search(r'Следующий лайк.*?в (\d{2}:\d{2})', text)
                    if time_match:
                        time_str = time_match.group(1)
                        hour, minute = map(int, time_str.split(':'))
                        next_time = self.get_current_time().replace(hour=hour, minute=minute, second=0, microsecond=0)
                        # Если указанное время уже прошло, значит это на следующий день
                        if next_time <= self.get_current_time():
                            next_time += datetime.timedelta(hours=4)
                        return next_time
                    return self.get_current_time() + datetime.timedelta(hours=4)

            return None

        except Exception as e:
            print(f"❌ Ошибка при извлечении времени для бота {bot_id}: {e}")
            print(f"Текст сообщения: {text}")
            return None
            
    async def update_bump_time(self, bot_id: str, next_bump: Optional[datetime.datetime], bot_name: str):
        """Обновляет время следующего бампа в базе данных"""
        try:
            if next_bump:
                await self.db.execute(
                    """
                    INSERT INTO bump_reminders (bot_id, next_bump, bot_name)
                    VALUES (?, ?, ?)
                    ON CONFLICT(bot_id) DO UPDATE SET
                    next_bump = ?, bot_name = ?
                    """,
                    bot_id, next_bump, bot_name,
                    next_bump, bot_name
                )
            else:
                await self.db.execute(
                    "DELETE FROM bump_reminders WHERE bot_id = ?",
                    bot_id
                )
        except Exception as e:
            print(f"❌ Ошибка при обновлении времени бампа: {e}")
            
    async def process_message_with_delay(self, message: discord.Message):
        """Обработка сообщения с задержкой для корректного отображения эмбедов"""
        try:
            # Получаем настройки из базы данных
            result_channel = await self.db.fetch_one(
                "SELECT value FROM settings WHERE category = 'bump_reminder' AND key = 'channel'"
            )
            result_bots = await self.db.fetch_one(
                "SELECT value FROM settings WHERE category = 'bump_reminder' AND key = 'allowed_bots'"
            )
            
            if not result_channel or not result_bots:
                return
                
            channel_id = int(result_channel['value'])
            bot_ids_str = result_bots['value'].strip('[]').replace(' ', '')
            allowed_bots = [int(bot_id.strip()) for bot_id in bot_ids_str.split(',') if bot_id.strip()]
            
            if message.author.id not in allowed_bots:
                return
                
            bot_name = self.bot_names.get(message.author.id, "unknown")
            
            # Извлекаем время следующего бампа
            next_bump = None
            
            # Проверяем эмбеды
            if message.embeds:
                for embed in message.embeds:
                    if embed.description:
                        print(f"📝 Проверяем эмбед от бота {bot_name}: {embed.description}")
                        next_bump = self.extract_time_from_text(embed.description, message.author.id)
                        if next_bump:
                            break
            
            # Если время не найдено в эмбедах, проверяем контент сообщения
            if not next_bump and message.content:
                print(f"📝 Проверяем контент от бота {bot_name}: {message.content}")
                next_bump = self.extract_time_from_text(message.content, message.author.id)
                
            # Обновляем время в базе данных
            if next_bump:
                print(f"✅ Найдено время бампа для бота {bot_name} ({message.author.id}): {next_bump}")
                await self.db.execute(
                    """
                    INSERT INTO bump_reminders (bot_id, bot_name, next_bump)
                    VALUES (?, ?, ?)
                    ON CONFLICT(bot_id) DO UPDATE SET
                    bot_name = ?, next_bump = ?
                    """,
                    str(message.author.id), bot_name, next_bump.isoformat(),
                    bot_name, next_bump.isoformat()
                )
                
                self.last_number[message.author.id] = next_bump
                
                # Отправляем уведомление
                channel = self.bot.get_channel(channel_id)
                if channel:
                    embed = discord.Embed(
                        title=f"{Emojis.SUCCESS} Время следующего бампа обновлено",
                        description=(
                            f"{Emojis.DOT} **Бот:** {bot_name}\n"
                            f"{Emojis.DOT} **Следующий бамп:** <t:{int(next_bump.timestamp())}:R>"
                        ),
                        color=self.colors['green']
                    )
                    await channel.send(embed=embed)
            else:
                print(f"❌ Не удалось найти время бампа в сообщении от бота {bot_name}")
                    
        except Exception as e:
            print(f"❌ Ошибка при обработке сообщения: {e}")
            import traceback
            traceback.print_exc()
            
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Обработчик сообщений"""
        if message.author.bot:
            await self.process_message_with_delay(message)
            
    @tasks.loop(minutes=1)
    async def check_bumps(self):
        """Проверка времени бампов"""
        try:
            bump_times = await self.db.fetch_all(
                "SELECT bot_id, bot_name, next_bump FROM bump_reminders"
            )
            
            if not bump_times:
                return
                
            current_time = self.get_current_time()
            
            for record in bump_times:
                try:
                    bot_id = int(record['bot_id'])
                    next_bump = datetime.datetime.fromisoformat(record['next_bump'])
                    bot_name = record['bot_name']
                    
                    if next_bump <= current_time:
                        result_channel = await self.db.fetch_one(
                            "SELECT value FROM settings WHERE category = 'bump_reminder' AND key = 'channel'"
                        )
                        
                        if not result_channel:
                            continue
                            
                        channel = self.bot.get_channel(int(result_channel['value']))
                        if not channel:
                            continue
                        
                        embed = discord.Embed(
                            title=f"{Emojis.DOT} Пора бампить!",
                            description=f"Можно бампить бота **{bot_name}**!",
                            color=self.colors['yellow']
                        )
                        
                        await channel.send(
                            f"<@&{self.bump_role}>" if self.bump_role is not None else "",
                            embed=embed
                        )
                        
                        await self.db.execute(
                            "DELETE FROM bump_reminders WHERE bot_id = ?",
                            str(bot_id)
                        )
                        
                except Exception as e:
                    print(f"❌ Ошибка при проверке бампа: {e}")
                    continue
                
        except Exception as e:
            print(f"❌ Ошибка в check_bumps: {e}")
            
    @commands.command(
        name="checkbump",
        aliases=["bump", "check_bump"],
        description="Проверить время следующего бампа"
    )
    async def check_bump(self, ctx: commands.Context, bot_name: str = None):
        """Проверка времени следующего бампа"""
        try:
            bump_times = await self.db.fetch_all(
                "SELECT bot_id, bot_name, next_bump FROM bump_reminders"
            )
            
            if not bump_times:
                embed = discord.Embed(
                    title=f"{Emojis.ERROR} Информация не найдена",
                    description="Нет данных о следующих бампах",
                    color=self.colors['red']
                )
                return await ctx.send(embed=embed)
            
            current_time = self.get_current_time()
            bumps_info = []
            
            for record in bump_times:
                try:
                    next_bump = datetime.datetime.fromisoformat(record['next_bump'])
                    record_bot_name = record['bot_name']
                    
                    if bot_name and bot_name.lower() != record_bot_name.lower():
                        continue
                        
                    time_left = next_bump - current_time
                    if time_left.total_seconds() > 0:
                        bumps_info.append(
                            f"{Emojis.DOT} **{record_bot_name}:** "
                            f"<t:{int(next_bump.timestamp())}:R>"
                        )
                        
                except Exception as e:
                    print(f"❌ Ошибка при обработке записи бампа: {e}")
                    continue
                    
            if not bumps_info:
                description = "Нет данных о следующих бампах"
                if bot_name:
                    description = f"Нет данных о следующем бампе для бота **{bot_name}**"
                    
                embed = discord.Embed(
                    title=f"{Emojis.ERROR} Информация не найдена",
                    description=description,
                    color=self.colors['red']
                )
            else:
                embed = discord.Embed(
                    title=f"{Emojis.DOT} Время следующих бампов",
                    description="\n".join(bumps_info),
                    color=self.colors['blue']
                )
                
            await ctx.send(embed=embed)
            
        except Exception as e:
            print(f"❌ Ошибка при выполнении команды check_bump: {e}")
            import traceback
            traceback.print_exc()

async def setup(bot):
    await bot.add_cog(BumpReminder(bot)) 