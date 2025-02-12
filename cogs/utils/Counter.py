import discord
from discord.ext import commands
from discord import app_commands
import re
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.constants import Emojis
from Niludetsu.utils.decorators import command_cooldown
import asyncio
from Niludetsu.database.db import Database

class Counter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.counter_channels = set()
        self.last_number = {}  # {channel_id: last_number}
        self.last_user = {}  # {channel_id: user_id}
        self.forum_channel_id = 1338883900877049876  # ID форум-канала
        self.counter_thread_id = 1338884903462375464  # ID ветки счетчика
        asyncio.create_task(self._initialize())

    async def _initialize(self):
        """Асинхронная инициализация"""
        await self.db.init()
        await self.load_channels()
        await self.load_numbers()
        await self.ensure_counter_thread()

    async def ensure_counter_thread(self):
        """Проверка и создание ветки счетчика если необходимо"""
        try:
            forum = self.bot.get_channel(self.forum_channel_id)
            if not forum:
                print(f"❌ Форум-канал не найден: {self.forum_channel_id}")
                return

            thread = self.bot.get_channel(self.counter_thread_id)
            if not thread:
                # Создаем новую ветку и эмбед
                embed = Embed(
                    title="🔢 Счетчик",
                    description="Начинаем считать с 1!\nТекущее число: 0",
                    color="DEFAULT"
                )
                thread = await forum.create_thread(
                    name="🔢 Счетчик",
                    embed=embed,
                    auto_archive_duration=4320  # 3 дня
                )
                self.counter_thread_id = thread.thread.id
                print(f"✅ Создана новая ветка счетчика: {thread.thread.id}")
                
                # Добавляем канал в базу данных
                await self.db.execute(
                    "INSERT OR IGNORE INTO counter_channels (channel_id, last_number) VALUES (?, ?)",
                    str(thread.thread.id), 0
                )
                self.counter_channels.add(thread.thread.id)
                self.last_number[thread.thread.id] = 0

        except Exception as e:
            print(f"❌ Ошибка при проверке ветки счетчика: {e}")

    async def load_numbers(self):
        """Загрузка последних чисел из базы данных"""
        try:
            results = await self.db.fetch_all(
                "SELECT channel_id, last_number FROM counter_channels"
            )
            for row in results:
                channel_id = int(row['channel_id'])
                self.last_number[channel_id] = row['last_number']
                print(f"✅ Загружен счетчик для канала {channel_id}: {row['last_number']}")
        except Exception as e:
            print(f"❌ Ошибка при загрузке счетчиков: {e}")

    async def update_counter_embed(self, channel_id: int, number: int):
        """Обновление эмбеда с текущим числом"""
        try:
            channel = self.bot.get_channel(channel_id)
            if channel:
                # Получаем историю сообщений
                async for message in channel.history(limit=10):
                    # Ищем сообщение от бота с эмбедом
                    if message.author == self.bot.user and message.embeds:
                        embed = message.embeds[0]
                        if embed.title == "🔢 Счетчик":
                            # Обновляем эмбед
                            new_embed = Embed(
                                title="🔢 Счетчик",
                                description=f"Текущее число: {number}",
                                color="DEFAULT"
                            )
                            await message.edit(embed=new_embed)
                            return
                
                # Если эмбед не найден, создаем новый
                embed = Embed(
                    title="🔢 Счетчик",
                    description=f"Текущее число: {number}",
                    color="DEFAULT"
                )
                await channel.send(embed=embed)
        except Exception as e:
            print(f"❌ Ошибка при обновлении эмбеда: {e}")

    async def save_number(self, channel_id: int, number: int, user_id: int):
        """Сохранение числа в базу данных"""
        try:
            # Обновляем только если канал существует
            if channel_id in self.counter_channels:
                await self.db.execute(
                    """
                    UPDATE counter_channels 
                    SET last_number = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE channel_id = ?
                    """,
                    number, str(channel_id)
                )
                self.last_number[channel_id] = number
                self.last_user[channel_id] = user_id
                
                # Обновляем эмбед
                await self.update_counter_embed(channel_id, number)
        except Exception as e:
            print(f"❌ Ошибка при сохранении счетчика: {e}")

    async def load_channels(self):
        """Загрузка каналов из базы данных"""
        try:
            results = await self.db.fetch_all(
                "SELECT channel_id FROM counter_channels"
            )
            self.counter_channels = set(int(row['channel_id']) for row in results)
        except Exception as e:
            print(f"❌ Ошибка при загрузке каналов счетчика: {e}")

    def evaluate_expression(self, expression: str) -> int:
        """Вычисление математического выражения"""
        try:
            # Удаляем все пробелы
            expression = expression.replace(" ", "")
            
            # Проверяем, является ли выражение просто числом
            if expression.isdigit():
                return int(expression)
                
            # Проверяем на допустимые символы
            if not re.match(r'^[0-9+\-*/()]+$', expression):
                return None
                
            # Безопасное вычисление выражения
            result = eval(expression, {"__builtins__": {}}, {})
            
            # Проверяем, что результат целое число
            if isinstance(result, (int, float)) and float(result).is_integer():
                return int(result)
            return None
        except:
            return None

    @commands.command(name="aecounter")
    @commands.has_permissions(administrator=True)
    async def aecounter(self, ctx):
        """Команда для установки счетчика"""
        try:
            # Проверяем/создаем ветку счетчика
            await self.ensure_counter_thread()
            thread = self.bot.get_channel(self.counter_thread_id)
            
            if thread:
                await ctx.send(
                    embed=Embed(
                        title=f"{Emojis.SUCCESS} Счетчик активирован",
                        description=f"Ветка счетчика: {thread.mention}\nТекущее значение: {self.last_number.get(thread.id, 0)}",
                        color="GREEN"
                    )
                )
            else:
                await ctx.send(
                    embed=Embed(
                        title=f"{Emojis.ERROR} Ошибка",
                        description="Не удалось создать или найти ветку счетчика",
                        color="RED"
                    )
                )
        except Exception as e:
            await ctx.send(
                embed=Embed(
                    title=f"{Emojis.ERROR} Ошибка",
                    description=f"Произошла ошибка: {str(e)}",
                    color="RED"
                )
            )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Игнорируем ботов и не счетчики
        if message.author.bot or message.channel.id not in self.counter_channels:
            return

        # Проверяем, не тот же ли пользователь пытается написать снова
        if message.channel.id in self.last_user and self.last_user[message.channel.id] == message.author.id:
            await message.delete()
            return

        # Пытаемся вычислить значение выражения
        result = self.evaluate_expression(message.content.strip())
        if result is None:
            await message.delete()
            return

        expected_number = self.last_number.get(message.channel.id, 0) + 1

        # Если результат правильный - сохраняем и ставим реакцию
        if result == expected_number:
            await self.save_number(message.channel.id, result, message.author.id)
            await message.add_reaction("✅")
            return

        # Иначе просто удаляем
        await message.delete()

    @commands.Cog.listener()
    async def on_ready(self):
        """Проверка каналов при запуске"""
        invalid_channels = set()
        for channel_id in self.counter_channels:
            channel = self.bot.get_channel(channel_id)
            if not channel:
                print(f"❌ Канал счетчика не найден: {channel_id}")
                invalid_channels.add(channel_id)
                
        # Удаляем несуществующие каналы
        self.counter_channels -= invalid_channels
        for channel_id in invalid_channels:
            if channel_id in self.last_number:
                del self.last_number[channel_id]
        
        if invalid_channels:
            await self.load_channels()

async def setup(bot):
    await bot.add_cog(Counter(bot)) 