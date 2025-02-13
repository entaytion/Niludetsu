import discord
from discord.ext import commands
from discord import app_commands
import re
from Niludetsu import (
    Embed,
    Emojis,
    cooldown
)
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
        
        # Загружаем ID ветки из базы данных
        result = await self.db.fetch_one(
            "SELECT thread_id FROM games WHERE game_type = 'counter' AND forum_id = ?",
            str(self.forum_channel_id)
        )
        if result and result['thread_id']:
            self.counter_thread_id = int(result['thread_id'])
            
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
            if self.counter_thread_id:
                thread = self.bot.get_channel(self.counter_thread_id)
                if thread and not thread.archived:  # Проверяем что ветка существует и не архивирована
                    return thread  # Ветка существует и доступна

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
            
            # Сохраняем ID ветки в базу данных
            await self.db.execute(
                """
                INSERT INTO games (channel_id, game_type, last_value, forum_id, thread_id, created_at, updated_at)
                VALUES (?, 'counter', ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT(channel_id) DO UPDATE SET 
                last_value = ?, forum_id = ?, thread_id = ?, updated_at = CURRENT_TIMESTAMP
                """,
                str(thread.thread.id), "0", str(self.forum_channel_id), str(thread.thread.id),
                "0", str(self.forum_channel_id), str(thread.thread.id)
            )
            
            self.last_number[thread.thread.id] = 0
            print(f"✅ Создана новая ветка счетчика: {thread.thread.id}")
            return thread

        except Exception as e:
            print(f"❌ Ошибка при проверке/создании ветки счетчика: {e}")
            return None

    async def load_numbers(self):
        """Загрузка последних чисел из базы данных"""
        rows = await self.db.fetch_all(
            "SELECT channel_id, last_value FROM games WHERE game_type = 'counter'"
        )
        for row in rows:
            channel_id = int(row['channel_id'])
            self.last_number[channel_id] = int(row['last_value'])
            # Очищаем last_user при загрузке
            self.last_user[channel_id] = None
            
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
        try:
            # Игнорируем ботов и сообщения не в ветке счетчика
            if message.author.bot or message.channel.id != self.counter_thread_id:
                return

            # Проверяем, не тот же ли пользователь пытается написать снова
            if message.channel.id in self.last_user and self.last_user[message.channel.id] == message.author.id:
                try:
                    await message.delete()
                except discord.NotFound:
                    pass
                return

            # Пытаемся вычислить значение выражения
            result = self.evaluate_expression(message.content.strip())
            if result is None:
                try:
                    await message.delete()
                except discord.NotFound:
                    pass
                return

            current_number = self.last_number.get(message.channel.id, 0)
            expected_number = current_number + 1

            # Если результат правильный - сохраняем и ставим реакцию
            if result == expected_number:
                # Сначала сохраняем в базу и обновляем состояние
                await self.save_number(message.channel.id, result, message.author.id)
                try:
                    await message.add_reaction("✅")
                except discord.NotFound:
                    pass
                return
            else:
                try:
                    await message.delete()
                except discord.NotFound:
                    pass
                return
        except Exception as e:
            print(f"❌ Ошибка в обработке сообщения счетчика: {e}")

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

    @app_commands.command(name="count", description="Подсчитать что-либо в сообщении")
    @app_commands.describe(
        text="Текст для подсчета",
        count_type="Что подсчитать (chars/words/lines)"
    )
    @cooldown(seconds=3)
    async def count(
        self,
        interaction: discord.Interaction,
        text: str,
        count_type: str = "chars"
    ):
        count_type = count_type.lower()
        if count_type not in ["chars", "words", "lines"]:
            return await interaction.response.send_message(
                embed=Embed(
                    title=f"{Emojis.ERROR} Ошибка",
                    description="Неверный тип подсчета! Используйте: chars/words/lines",
                    color="RED"
                ),
                ephemeral=True
            )

        result = 0
        if count_type == "chars":
            result = len(text)
        elif count_type == "words":
            result = len(text.split())
        else:  # lines
            result = len(text.splitlines())

        count_types = {
            "chars": "символов",
            "words": "слов",
            "lines": "строк"
        }

        await interaction.response.send_message(
            embed=Embed(
                title=f"{Emojis.SUCCESS} Результат подсчета",
                description=f"В тексте `{result}` {count_types[count_type]}",
                color="GREEN"
            )
        )

async def setup(bot):
    await bot.add_cog(Counter(bot)) 