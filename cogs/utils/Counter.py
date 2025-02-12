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
        self.last_number = {}  # {channel_id: last_number}
        self.last_user = {}  # {channel_id: user_id}
        self.forum_channel_id = 1338883900877049876  # ID форум-канала
        self.counter_thread_id = None  # ID ветки счетчика
        self.ready = False
        asyncio.create_task(self._initialize())

    async def _initialize(self):
        """Асинхронная инициализация"""
        await self.bot.wait_until_ready()  # Ждем пока бот будет готов
        await self.db.init()
        await self.load_numbers()
        self.ready = True
        await self.ensure_counter_thread()

    async def ensure_counter_thread(self):
        """Проверка и создание ветки счетчика если необходимо"""
        if not self.ready:
            return

        try:
            # Сначала пытаемся получить форум-канал
            forum = self.bot.get_channel(self.forum_channel_id)
            if not forum:
                print(f"❌ Форум-канал не найден: {self.forum_channel_id}")
                return

            # Пытаемся получить существующую ветку
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
                    """INSERT INTO games 
                       (channel_id, game_type, last_value, forum_id, thread_id) 
                       VALUES (?, 'counter', ?, ?, ?)
                       ON CONFLICT(channel_id) DO UPDATE SET 
                       last_value = ?, forum_id = ?, thread_id = ?""",
                    str(thread.thread.id), "0", 
                    str(self.forum_channel_id), str(self.counter_thread_id),
                    "0", str(self.forum_channel_id), str(self.counter_thread_id)
                )
                self.last_number[thread.thread.id] = 0

        except Exception as e:
            print(f"❌ Ошибка при проверке/создании ветки счетчика: {e}")

    async def load_numbers(self):
        """Загрузка последних чисел из базы данных"""
        rows = await self.db.fetch_all(
            "SELECT channel_id, last_value FROM games WHERE game_type = 'counter'"
        )
        self.last_number = {int(row['channel_id']): int(row['last_value']) for row in rows}
        if self.last_number:
            # Берем первый и единственный канал
            self.counter_thread_id = int(list(self.last_number.keys())[0])

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
        await self.db.execute(
            """INSERT INTO games (channel_id, game_type, last_value, updated_at) 
               VALUES (?, 'counter', ?, CURRENT_TIMESTAMP)
               ON CONFLICT(channel_id) DO UPDATE SET 
               last_value = ?, updated_at = CURRENT_TIMESTAMP""",
            str(channel_id), str(number), str(number)
        )
        self.last_number[channel_id] = number
        self.last_user[channel_id] = user_id
        
        # Обновляем эмбед
        await self.update_counter_embed(channel_id, number)

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

    async def setup_counter(self, ctx):
        """Настройка счетчика"""
        # Проверяем существующую ветку
        thread = await self.ensure_counter_thread()
        
        if thread:
            return await ctx.send(
                embed=Embed(
                    title=f"{Emojis.ERROR} Ошибка",
                    description=f"Счетчик уже активирован в ветке {thread.mention}\n"
                              f"Текущее значение: {self.last_number.get(thread.id, 0)}",
                    color="RED"
                )
            )

        # Если ветки нет, создаем новую
        thread = await self.ensure_counter_thread()
        
        if thread:
            return await ctx.send(
                embed=Embed(
                    title=f"{Emojis.SUCCESS} Счетчик активирован",
                    description=f"Создана новая ветка: {thread.mention}\n"
                              f"Текущее значение: 0",
                    color="GREEN"
                )
            )
        else:
            return await ctx.send(
                embed=Embed(
                    title=f"{Emojis.ERROR} Ошибка",
                    description="Не удалось создать ветку счетчика",
                    color="RED"
                )
            )

    async def show_info(self, ctx):
        """Показать информацию о счетчике"""
        thread = self.bot.get_channel(self.counter_thread_id)
        if thread and thread.id in self.last_number:
            return await ctx.send(
                embed=Embed(
                    title="🔢 Информация о счетчике",
                    description=(
                        f"**Канал:** {thread.mention}\n"
                        f"**Текущее значение:** {self.last_number[thread.id]}\n"
                        f"**Статус:** Активен"
                    ),
                    color="BLUE"
                )
            )
        else:
            return await ctx.send(
                embed=Embed(
                    title="🔢 Информация о счетчике",
                    description="Счетчик не настроен. Используйте `!games counter setup`",
                    color="YELLOW"
                )
            )

    async def delete_counter(self, ctx):
        """Удалить счетчик"""
        if self.counter_thread_id:
            await self.db.execute(
                "DELETE FROM games WHERE channel_id = ? AND game_type = 'counter'",
                str(self.counter_thread_id)
            )
            if self.counter_thread_id in self.last_number:
                del self.last_number[self.counter_thread_id]
            return await ctx.send(
                embed=Embed(
                    title=f"{Emojis.SUCCESS} Счетчик удален",
                    description="Все данные счетчика были удалены",
                    color="GREEN"
                )
            )
        else:
            return await ctx.send(
                embed=Embed(
                    title=f"{Emojis.ERROR} Ошибка",
                    description="Счетчик не был настроен",
                    color="RED"
                )
            )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Игнорируем ботов и сообщения не в ветке счетчика
        if message.author.bot or message.channel.id != self.counter_thread_id:
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
        if not self.ready:
            return

        # Проверяем существование ветки счетчика
        if self.counter_thread_id:
            channel = self.bot.get_channel(self.counter_thread_id)
            if not channel:
                print(f"❌ Ветка счетчика не найдена: {self.counter_thread_id}")
                # Удаляем из базы данных
                await self.db.execute(
                    "DELETE FROM games WHERE channel_id = ? AND game_type = 'counter'",
                    str(self.counter_thread_id)
                )
                if self.counter_thread_id in self.last_number:
                    del self.last_number[self.counter_thread_id]
                self.counter_thread_id = None
                # Пробуем создать новую ветку
                await self.ensure_counter_thread()

async def setup(bot):
    await bot.add_cog(Counter(bot)) 