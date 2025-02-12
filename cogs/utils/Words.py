import discord
from discord.ext import commands
import asyncio
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.constants import Emojis
from Niludetsu.database.db import Database
import re

class Words(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.words_channels = set()
        self.last_word = {}  # {channel_id: last_word}
        self.last_user = {}  # {channel_id: user_id}
        self.used_words = {}  # {channel_id: set(words)}
        self.forum_channel_id = 1338883900877049876  # ID форум-канала
        self.words_thread_id = None  # ID ветки для игры в слова
        asyncio.create_task(self._initialize())

    async def _initialize(self):
        """Асинхронная инициализация"""
        await self.db.init()
        await self.load_channels()
        await self.load_words()
        await self.ensure_words_thread()

    async def ensure_words_thread(self):
        """Проверка и создание ветки для игры в слова если необходимо"""
        try:
            forum = self.bot.get_channel(self.forum_channel_id)
            if not forum:
                print(f"❌ Форум-канал не найден: {self.forum_channel_id}")
                return

            # Ищем существующую ветку с игрой в слова
            for thread in forum.threads:
                if thread.name == "🔤 Игра в слова":
                    self.words_thread_id = thread.id
                    print(f"✅ Найдена существующая ветка для игры в слова: {thread.id}")
                    break

            if not self.words_thread_id:
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
                    "INSERT OR IGNORE INTO words_channels (channel_id, last_word) VALUES (?, ?)",
                    str(thread.thread.id), ""
                )
                self.words_channels.add(thread.thread.id)
                self.last_word[thread.thread.id] = ""
                self.used_words[thread.thread.id] = set()

        except Exception as e:
            print(f"❌ Ошибка при проверке ветки для игры в слова: {e}")

    async def load_words(self):
        """Загрузка последних слов из базы данных"""
        try:
            results = await self.db.fetch_all(
                "SELECT channel_id, last_word, used_words FROM words_channels"
            )
            for row in results:
                channel_id = int(row['channel_id'])
                self.last_word[channel_id] = row['last_word']
                self.used_words[channel_id] = set(row['used_words'].split(',')) if row['used_words'] else set()
                print(f"✅ Загружены данные для канала {channel_id}")
        except Exception as e:
            print(f"❌ Ошибка при загрузке данных: {e}")

    async def save_word(self, channel_id: int, word: str, user_id: int):
        """Сохранение слова в базу данных"""
        try:
            if channel_id in self.words_channels:
                # Добавляем слово в использованные
                if channel_id not in self.used_words:
                    self.used_words[channel_id] = set()
                self.used_words[channel_id].add(word.lower())
                
                # Обновляем базу данных
                used_words_str = ','.join(self.used_words[channel_id])
                await self.db.execute(
                    """
                    UPDATE words_channels 
                    SET last_word = ?, used_words = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE channel_id = ?
                    """,
                    word.lower(), used_words_str, str(channel_id)
                )
                self.last_word[channel_id] = word.lower()
                self.last_user[channel_id] = user_id
                
                # Обновляем эмбед
                await self.update_words_embed(channel_id)
        except Exception as e:
            print(f"❌ Ошибка при сохранении слова: {e}")

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
                                          f"{Emojis.DOT} Следующее слово должно начинаться на: `{self.last_word[channel_id][-1].upper()}`\n"
                                          f"{Emojis.DOT} Использовано слов: `{len(self.used_words[channel_id])}`",
                                color="DEFAULT"
                            )
                            await message.edit(embed=new_embed)
                            return
        except Exception as e:
            print(f"❌ Ошибка при обновлении эмбеда: {e}")

    async def load_channels(self):
        """Загрузка каналов из базы данных"""
        try:
            results = await self.db.fetch_all(
                "SELECT channel_id FROM words_channels"
            )
            self.words_channels = set(int(row['channel_id']) for row in results)
        except Exception as e:
            print(f"❌ Ошибка при загрузке каналов: {e}")

    def is_valid_word(self, word: str) -> bool:
        """Проверка валидности слова"""
        # Только буквы русского алфавита
        return bool(re.match(r'^[а-яёА-ЯЁ]+$', word))

    @commands.command(name="aewords")
    @commands.has_permissions(administrator=True)
    async def aewords(self, ctx):
        """Команда для установки игры в слова"""
        try:
            # Проверяем/создаем ветку
            await self.ensure_words_thread()
            thread = self.bot.get_channel(self.words_thread_id)
            
            if thread:
                await ctx.send(
                    embed=Embed(
                        title=f"{Emojis.SUCCESS} Игра в слова активирована",
                        description=f"Ветка для игры: {thread.mention}\n"
                                  f"Последнее слово: `{self.last_word.get(thread.id, 'Игра не начата')}`",
                        color="GREEN"
                    )
                )
            else:
                await ctx.send(
                    embed=Embed(
                        title=f"{Emojis.ERROR} Ошибка",
                        description="Не удалось создать или найти ветку для игры",
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
        # Игнорируем ботов и не игровые каналы
        if message.author.bot or message.channel.id not in self.words_channels:
            return

        # Проверяем, не тот же ли пользователь пытается написать снова
        if message.channel.id in self.last_user and self.last_user[message.channel.id] == message.author.id:
            await message.delete()
            return

        word = message.content.strip().lower()

        # Проверяем валидность слова
        if not self.is_valid_word(word):
            await message.delete()
            return

        # Проверяем, не было ли уже такого слова
        if word in self.used_words.get(message.channel.id, set()):
            await message.delete()
            await message.channel.send(
                embed=Embed(
                    title=f"{Emojis.ERROR} Ошибка",
                    description=f"Слово `{word}` уже было использовано!",
                    color="RED"
                ),
                delete_after=5
            )
            return

        # Проверяем первую букву слова
        last_word = self.last_word.get(message.channel.id, "")
        if last_word and word[0] != last_word[-1]:
            await message.delete()
            await message.channel.send(
                embed=Embed(
                    title=f"{Emojis.ERROR} Ошибка",
                    description=f"Слово должно начинаться на букву `{last_word[-1].upper()}`!",
                    color="RED"
                ),
                delete_after=5
            )
            return

        # Если все проверки пройдены, сохраняем слово
        await self.save_word(message.channel.id, word, message.author.id)
        await message.add_reaction("✅")

    @commands.Cog.listener()
    async def on_ready(self):
        """Проверка каналов при запуске"""
        invalid_channels = set()
        for channel_id in self.words_channels:
            channel = self.bot.get_channel(channel_id)
            if not channel:
                print(f"❌ Канал игры в слова не найден: {channel_id}")
                invalid_channels.add(channel_id)
                
        # Удаляем несуществующие каналы
        self.words_channels -= invalid_channels
        for channel_id in invalid_channels:
            if channel_id in self.last_word:
                del self.last_word[channel_id]
            if channel_id in self.used_words:
                del self.used_words[channel_id]
        
        if invalid_channels:
            await self.load_channels()

async def setup(bot):
    await bot.add_cog(Words(bot)) 