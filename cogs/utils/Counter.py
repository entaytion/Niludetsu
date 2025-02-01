import discord
from discord.ext import commands
from discord import app_commands
import re
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.emojis import EMOJIS
from Niludetsu.utils.decorators import command_cooldown
import asyncio
from Niludetsu.database.db import Database

class Counter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.counter_channels = set()
        self.last_number = {}  # {channel_id: last_number}
        asyncio.create_task(self._initialize())

    async def _initialize(self):
        """Асинхронная инициализация"""
        await self.db.init()
        await self.load_channels()
        await self.load_numbers()

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

    async def save_number(self, channel_id: int, number: int):
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
        """Проверка является ли строка числом"""
        try:
            # Проверяем, является ли строка положительным целым числом
            if expression.isdigit():
                return int(expression)
            return None
        except:
            return None

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Игнорируем ботов и не счетчики
        if message.author.bot or message.channel.id not in self.counter_channels:
            return

        # Проверяем является ли сообщение числом
        if not message.content.strip().isdigit():
            await message.delete()
            return

        number = int(message.content.strip())
        expected_number = self.last_number.get(message.channel.id, 0) + 1

        # Если число правильное - сохраняем и ставим реакцию
        if number == expected_number:
            self.last_number[message.channel.id] = number
            await self.save_number(message.channel.id, number)
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