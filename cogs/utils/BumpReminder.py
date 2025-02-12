import discord
from discord.ext import commands, tasks
from discord import app_commands
import yaml
import datetime
import re
import asyncio
from typing import Optional, Dict
import pytz

class BumpReminder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = self.load_config()
        self.check_bumps.start()
        self.processing_messages: Dict[int, asyncio.Task] = {}
        # Устанавливаем часовой пояс UTC+2
        self.timezone = pytz.timezone('Europe/Kiev')  # UTC+2
        # Загружаем список разрешенных ботов из конфига
        self.allowed_bots = self.config.get('bump_reminder', {}).get('allowed_bots', [])
        # Загружаем или инициализируем времена бампов
        self.bump_times = self.config.get('bump_reminder', {}).get('bump_times', {})
        if not self.allowed_bots:
            print("[Bump Reminder] Предупреждение: список разрешенных ботов пуст!")
        
    def load_config(self) -> dict:
        """Загрузка конфигурации из файла"""
        try:
            with open('data/config.yaml', 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Ошибка загрузки конфига: {e}")
            return {}
            
    def cog_unload(self):
        self.check_bumps.cancel()
        # Отменяем все ожидающие задачи
        for task in self.processing_messages.values():
            task.cancel()

    def get_current_time(self) -> datetime.datetime:
        """Получение текущего времени с учетом часового пояса"""
        return datetime.datetime.now(self.timezone)

    def localize_time(self, dt: datetime.datetime) -> datetime.datetime:
        """Добавление информации о часовом поясе к datetime объекту"""
        if dt.tzinfo is None:
            return self.timezone.localize(dt)
        return dt

    def parse_discord_timestamp(self, content: str) -> Optional[datetime.datetime]:
        """Парсинг Discord timestamp из сообщения с учетом часового пояса"""
        timestamp_match = re.search(r'<t:(\d+):', content)
        if timestamp_match:
            try:
                timestamp = int(timestamp_match.group(1))
                # Преобразуем UTC timestamp в нужное время (UTC+2)
                utc_time = datetime.datetime.fromtimestamp(timestamp, tz=pytz.UTC)
                local_time = utc_time.astimezone(self.timezone)
                print(f"[Bump Reminder] UTC время: {utc_time}, Локальное время: {local_time}")
                return local_time
            except (ValueError, OSError) as e:
                print(f"[Bump Reminder] Ошибка при парсинге timestamp: {e}")
        return None

    def extract_time_from_text(self, text: str, bot_id: int) -> Optional[datetime.datetime]:
        """Извлечение времени из текста"""
        if not text:
            return None
            
        print(f"[Bump Reminder] Анализ текста: {text}")
        
        # Специальная обработка для DISBOARD
        if bot_id == 302050872383242240:  # DISBOARD
            if "bump done" in text.lower():
                # Если найдено "Bump done!", устанавливаем таймер на 2 часа
                current_time = self.get_current_time()
                next_bump = current_time + datetime.timedelta(hours=2)
                print(f"[Bump Reminder] DISBOARD: Bump выполнен, следующий через 2 часа в {next_bump}")
                return next_bump
                
        # Специальная обработка для Server Monitoring
        if bot_id == 315926021457051650:  # Server Monitoring
            # Ищем формат "will be available in XX:XX:XX"
            time_match = re.search(r'will be available in (\d{2}):(\d{2}):(\d{2})', text)
            if time_match:
                hours, minutes, seconds = map(int, time_match.groups())
                current_time = self.get_current_time()
                next_bump = current_time + datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds)
                print(f"[Bump Reminder] Server Monitoring: Следующий бамп через {hours}:{minutes}:{seconds} в {next_bump}")
                return next_bump
            # Оставляем также проверку на "server bumped by" как запасной вариант
            elif "server bumped by" in text.lower():
                current_time = self.get_current_time()
                next_bump = current_time + datetime.timedelta(hours=4)
                print(f"[Bump Reminder] Server Monitoring: Bump выполнен, следующий через 4 часа в {next_bump}")
                return next_bump
                
        # Специальная обработка для SD.C Monitoring
        if bot_id == 464272403766444044:  # SD.C Monitoring
            # Ищем время фиксации в тексте
            if "Время фиксации апа:" in text.lower():
                current_time = self.get_current_time()
                next_bump = current_time + datetime.timedelta(hours=4)
                print(f"[Bump Reminder] SD.C Monitoring: Зафиксирован ап, следующий через 4 часа в {next_bump}")
                return next_bump
            # Ищем Discord timestamp
            timestamp_match = re.search(r'<t:(\d+):', text)
            if timestamp_match:
                timestamp = int(timestamp_match.group(1))
                # Преобразуем UTC timestamp в локальное время и добавляем 4 часа
                utc_time = datetime.datetime.fromtimestamp(timestamp, tz=pytz.UTC)
                next_bump = utc_time.astimezone(self.timezone) + datetime.timedelta(hours=4)
                print(f"[Bump Reminder] SD.C Monitoring: Следующий бамп в {next_bump}")
                return next_bump
            # Запасной вариант - если формат сообщения изменился
            elif "up" in text.lower():
                current_time = self.get_current_time()
                next_bump = current_time + datetime.timedelta(hours=4)  # Стандартное время
                print(f"[Bump Reminder] SD.C Monitoring: Формат не распознан, ставим стандартные 4 часа, в {next_bump}")
                return next_bump
        
        # Проверяем Discord timestamp
        next_bump = self.parse_discord_timestamp(text)
        if next_bump:
            print(f"[Bump Reminder] Найден Discord timestamp, следующий бамп в {next_bump}")
            return next_bump

        # Проверяем обычные форматы времени
        patterns = [
            (r'поднять сервер только через (\d+) час[а|ов].*?(\d{1,2}:\d{2})', True),
            (r'поднять сервер.*?через (\d+) час[а|ов].*?(\d{1,2}:\d{2})', True),
            (r'через (\d+) час[а|ов].*?(\d{1,2}:\d{2})', True),
            (r'только через (\d+) час[а|ов].*?(\d{1,2}:\d{2})', True),
            (r'поднять сервер только через (\d+) час[а|ов]', False),
            (r'через (\d+) час[а|ов]', False),
            (r'(\d{1,2}:\d{2})', False)  # Просто время
        ]
        
        text_lower = text.lower()
        current_time = self.get_current_time()
        
        for pattern, has_time in patterns:
            match = re.search(pattern, text_lower)
            if match:
                print(f"[Bump Reminder] Найдено совпадение по паттерну: {pattern}")
                try:
                    if has_time:
                        hours_until = int(match.group(1))
                        time_str = match.group(2)
                        print(f"[Bump Reminder] Найдено время: {time_str}, через {hours_until} часов")
                        hours, minutes = map(int, time_str.split(':'))
                        next_bump = current_time.replace(hour=hours, minute=minutes, second=0, microsecond=0)
                        if next_bump < current_time:
                            next_bump += datetime.timedelta(days=1)
                    else:
                        if len(match.groups()) == 1 and ':' in match.group(1):
                            # Если нашли просто время (ЧЧ:ММ)
                            time_str = match.group(1)
                            print(f"[Bump Reminder] Найдено время: {time_str}")
                            hours, minutes = map(int, time_str.split(':'))
                            next_bump = current_time.replace(hour=hours, minute=minutes, second=0, microsecond=0)
                            if next_bump < current_time:
                                next_bump += datetime.timedelta(days=1)
                        else:
                            # Если нашли "через X часов"
                            hours_until = int(match.group(1))
                            print(f"[Bump Reminder] Через {hours_until} часов")
                            next_bump = current_time + datetime.timedelta(hours=hours_until)
                    
                    print(f"[Bump Reminder] Рассчитанное время следующего бампа: {next_bump}")
                    return next_bump
                except (ValueError, IndexError) as e:
                    print(f"[Bump Reminder] Ошибка при обработке времени: {e}")
                    continue
        
        return None
                
    def save_config(self):
        """Сохранение конфигурации в файл"""
        try:
            with open('data/config.yaml', 'w', encoding='utf-8') as f:
                yaml.safe_dump(self.config, f, allow_unicode=True)
        except Exception as e:
            print(f"[Bump Reminder] Ошибка сохранения конфига: {e}")

    def update_bump_time(self, bot_id: str, next_bump: Optional[datetime.datetime], bot_name: str):
        """Обновление времени следующего бампа в конфиге"""
        if 'bump_reminder' not in self.config:
            self.config['bump_reminder'] = {}
        if 'bump_times' not in self.config['bump_reminder']:
            self.config['bump_reminder']['bump_times'] = {}
            
        self.config['bump_reminder']['bump_times'][bot_id] = {
            "next_bump": next_bump.strftime('%Y-%m-%d %H:%M:%S%z') if next_bump else None,
            "bot_name": bot_name
        }
        self.bump_times = self.config['bump_reminder']['bump_times']
        self.save_config()

    async def process_message_with_delay(self, message: discord.Message):
        """Обработка сообщения с задержкой"""
        try:
            # Ждем 5 секунд
            await asyncio.sleep(5)
            
            # Пытаемся получить обновленное сообщение
            try:
                message = await message.channel.fetch_message(message.id)
            except discord.NotFound:
                return
            except Exception as e:
                return

            next_bump = None
            
            # Проверяем основной контент сообщения
            if message.content.strip():
                next_bump = self.extract_time_from_text(message.content, message.author.id)
                
            # Проверяем эмбеды, если время не найдено в контенте
            if not next_bump and message.embeds:
                for embed in message.embeds:
                    # Проверяем заголовок
                    if embed.title:
                        next_bump = self.extract_time_from_text(embed.title, message.author.id)
                        if next_bump:
                            break
                    
                    # Проверяем описание
                    if not next_bump and embed.description:
                        next_bump = self.extract_time_from_text(embed.description, message.author.id)
                        if next_bump:
                            break
                    
                    # Проверяем поля
                    if not next_bump and embed.fields:
                        for field in embed.fields:
                            next_bump = self.extract_time_from_text(field.value, message.author.id)
                            if not next_bump:
                                next_bump = self.extract_time_from_text(field.name, message.author.id)
                            if next_bump:
                                break
                        
                    if next_bump:
                        break
            
            if next_bump:
                bot_id = str(message.author.id)
                self.update_bump_time(bot_id, next_bump, message.author.name)

        except asyncio.CancelledError:
            return
        except Exception as e:
            return
        finally:
            # Удаляем задачу из списка обрабатываемых
            if message.id in self.processing_messages:
                del self.processing_messages[message.id]

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Обработчик сообщений для отслеживания бампов"""
        if not message.author.bot or message.author.id not in self.allowed_bots:
            return

        # Создаем новую задачу для обработки сообщения с задержкой
        task = asyncio.create_task(self.process_message_with_delay(message))
        self.processing_messages[message.id] = task

    @tasks.loop(minutes=1)
    async def check_bumps(self):
        """Проверка времени бампов"""
        current_time = self.get_current_time()
        
        for bot_id, bump_data in list(self.bump_times.items()):
            if not bump_data['next_bump']:
                continue
                
            next_bump = datetime.datetime.strptime(bump_data['next_bump'], '%Y-%m-%d %H:%M:%S%z')
            if current_time >= next_bump:
                notify_channel = self.bot.get_channel(1125546970522583070)
                if notify_channel:
                    owner_id = self.config.get('settings', {}).get('owner_id')
                    if owner_id:
                        await notify_channel.send(
                            f"<@{owner_id}>, пора сделать бамп для бота {bump_data['bot_name']}!"
                        )
                        # Сбрасываем время бампа
                        self.update_bump_time(bot_id, None, bump_data['bot_name'])
                        break

    @commands.command(
        name="checkbump",
        description="Показывает информацию о следующем бампе",
        aliases=['bump']
    )
    async def check_bump(self, ctx, bot_name: str = None):
        """Показывает информацию о следующем бампе
        
        Параметры:
        ---------------
        bot_name: Имя бота для проверки (необязательно)
        """
        current_time = self.get_current_time()
        has_bumps = False
        
        embed = discord.Embed(
            title="📊 Информация о бампах",
            color=0x3498db,  # Синий цвет
            timestamp=current_time
        )
        
        for bot_id, bump_data in self.bump_times.items():
            if not bump_data['next_bump']:
                continue
                
            if bot_name and bot_name.lower() not in bump_data['bot_name'].lower():
                continue
                
            next_bump = datetime.datetime.strptime(bump_data['next_bump'], '%Y-%m-%d %H:%M:%S%z')
            time_until = next_bump - current_time
            hours, remainder = divmod(int(time_until.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            
            if hours > 0:
                time_str = f"{hours} ч. {minutes} мин."
            else:
                time_str = f"{minutes} мин. {seconds} сек."
            
            has_bumps = True
            
            # Добавляем поле для каждого бота
            embed.add_field(
                name=f"🤖 {bump_data['bot_name']}",
                value=f"⏰ **Следующий бамп:** `{next_bump.strftime('%H:%M')}`\n"
                      f"⏳ **Осталось ждать:** `{time_str}`",
                inline=False
            )
            
        if not has_bumps:
            embed.description = "Нет запланированных бампов"
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(BumpReminder(bot)) 