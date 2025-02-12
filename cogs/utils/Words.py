import discord
from discord.ext import commands
import asyncio
import json
import re
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.constants import Emojis
from Niludetsu.database.db import Database

class Words(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.last_word = {}  # {channel_id: last_word}
        self.last_user = {}  # {channel_id: user_id}
        self.used_words = {}  # {channel_id: set(words)}
        self.forum_channel_id = 1338883900877049876  # ID форум-канала
        self.words_thread_id = None  # ID ветки для игры в слова
        self.ready = False
        asyncio.create_task(self._initialize())

    async def _initialize(self):
        """Асинхронная инициализация"""
        await self.bot.wait_until_ready()
        await self.db.init()
        await self.load_words()
        self.ready = True
        await self.ensure_words_thread()

    async def ensure_words_thread(self):
        """Проверка и создание ветки для игры в слова если необходимо"""
        if not self.ready:
            return

        try:
            forum = self.bot.get_channel(self.forum_channel_id)
            if not forum:
                print(f"❌ Форум-канал не найден: {self.forum_channel_id}")
                return

            # Пытаемся получить существующую ветку
            thread = self.bot.get_channel(self.words_thread_id)
            if not thread:
                # Создаем новую ветку и эмбед
                embed = Embed(
                    title="🔤 Игра в слова",
                    description="Правила игры:\n"
                               f"{Emojis.DOT} Каждое следующее слово должно начинаться на последнюю букву предыдущего\n"
                               f"{Emojis.DOT} Нельзя использовать уже названные слова\n"
                               f"{Emojis.DOT} Один игрок не может писать два слова подряд\n"
                               f"{Emojis.DOT} Используйте только существительные в единственном числе\n\n"
                               "Начинаем игру! Напишите любое слово для старта.",
                    color="DEFAULT"
                )
                thread = await forum.create_thread(
                    name="🔤 Игра в слова",
                    embed=embed,
                    auto_archive_duration=4320  # 3 дня
                )
                self.words_thread_id = thread.thread.id
                print(f"✅ Создана новая ветка для игры в слова: {thread.thread.id}")
                
                # Добавляем канал в базу данных
                await self.db.execute(
                    """INSERT INTO games 
                       (channel_id, game_type, last_value, used_values) 
                       VALUES (?, 'words', '', '[]')
                       ON CONFLICT(channel_id) DO UPDATE SET 
                       last_value = '', used_values = '[]'""",
                    str(thread.thread.id)
                )
                self.last_word[thread.thread.id] = ""
                self.used_words[thread.thread.id] = set()

        except Exception as e:
            print(f"❌ Ошибка при проверке/создании ветки для игры в слова: {e}")

    async def load_words(self):
        """Загрузка данных из базы данных"""
        try:
            rows = await self.db.fetch_all(
                "SELECT channel_id, last_value, used_values FROM games WHERE game_type = 'words'"
            )
            for row in rows:
                channel_id = int(row['channel_id'])
                self.last_word[channel_id] = row['last_value']
                self.used_words[channel_id] = set(json.loads(row['used_values'])) if row['used_values'] else set()
                self.words_thread_id = channel_id  # Берем первый найденный ID
                print(f"✅ Загружены данные для канала {channel_id}")
        except Exception as e:
            print(f"❌ Ошибка при загрузке данных: {e}")

    async def update_words_embed(self, channel_id: int):
        """Обновление эмбеда с текущей статистикой игры"""
        try:
            channel = self.bot.get_channel(channel_id)
            if channel:
                # Получаем историю сообщений
                async for message in channel.history(limit=10):
                    # Ищем сообщение от бота с эмбедом
                    if message.author == self.bot.user and message.embeds:
                        embed = message.embeds[0]
                        if embed.title == "🔤 Игра в слова":
                            # Обновляем эмбед
                            new_embed = Embed(
                                title="🔤 Игра в слова",
                                description=f"Текущая статистика:\n"
                                          f"{Emojis.DOT} Последнее слово: `{self.last_word[channel_id]}`\n"
                                          f"{Emojis.DOT} Следующее слово должно начинаться на: `{self.last_word[channel_id][-1].upper() if self.last_word[channel_id] else 'Любая буква'}`\n"
                                          f"{Emojis.DOT} Использовано слов: `{len(self.used_words[channel_id])}`",
                                color="DEFAULT"
                            )
                            await message.edit(embed=new_embed)
                            return
        except Exception as e:
            print(f"❌ Ошибка при обновлении эмбеда: {e}")

    def is_valid_word(self, word: str) -> bool:
        """Проверка валидности слова"""
        # Только буквы русского алфавита
        return bool(re.match(r'^[а-яёА-ЯЁ]+$', word))

    async def save_word(self, channel_id: int, word: str, user_id: int):
        """Сохранение слова в базу данных"""
        if channel_id not in self.used_words:
            self.used_words[channel_id] = set()
        self.used_words[channel_id].add(word.lower())
        
        await self.db.execute(
            """INSERT INTO games (channel_id, game_type, last_value, used_values, updated_at) 
               VALUES (?, 'words', ?, ?, CURRENT_TIMESTAMP)
               ON CONFLICT(channel_id) DO UPDATE SET 
               last_value = ?, used_values = ?, updated_at = CURRENT_TIMESTAMP""",
            str(channel_id), word, json.dumps(list(self.used_words[channel_id])),
            word, json.dumps(list(self.used_words[channel_id]))
        )
        self.last_word[channel_id] = word
        self.last_user[channel_id] = user_id
        
        # Обновляем эмбед
        await self.update_words_embed(channel_id)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Игнорируем ботов и не игровые каналы
        if message.author.bot or message.channel.id != self.words_thread_id:
            return

        # Проверяем, не тот же ли пользователь пытается написать снова
        if message.channel.id in self.last_user and self.last_user[message.channel.id] == message.author.id:
            await message.delete()
            return

        word = message.content.strip().lower()
        
        # Проверяем, что сообщение содержит только одно слово
        if len(word.split()) > 1:
            await message.delete()
            return

        # Проверяем валидность слова
        if not self.is_valid_word(word):
            await message.delete()
            return

        # Проверяем, что слово не было использовано ранее
        if word in self.used_words.get(message.channel.id, set()):
            await message.delete()
            return

        # Проверяем, что слово начинается с последней буквы предыдущего слова
        last_word = self.last_word.get(message.channel.id, "")
        if last_word and word[0] != last_word[-1]:
            await message.delete()
            return

        # Сохраняем слово и ставим реакцию
        await self.save_word(message.channel.id, word, message.author.id)
        await message.add_reaction("✅")

    @commands.Cog.listener()
    async def on_ready(self):
        """Проверка каналов при запуске"""
        if not self.ready:
            return

        # Проверяем существование ветки
        if self.words_thread_id:
            channel = self.bot.get_channel(self.words_thread_id)
            if not channel:
                print(f"❌ Ветка игры в слова не найдена: {self.words_thread_id}")
                # Удаляем из базы данных
                await self.db.execute(
                    "DELETE FROM games WHERE channel_id = ? AND game_type = 'words'",
                    str(self.words_thread_id)
                )
                if self.words_thread_id in self.last_word:
                    del self.last_word[self.words_thread_id]
                if self.words_thread_id in self.used_words:
                    del self.used_words[self.words_thread_id]
                self.words_thread_id = None
                # Пробуем создать новую ветку
                await self.ensure_words_thread()

async def setup(bot):
    await bot.add_cog(Words(bot)) 