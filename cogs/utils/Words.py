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
        self.forum_channel_id = 1338883900877049876  # ID форум-канала
        self.words_thread_id = None  # ID ветки для игры в слова
        self.ready = False
        asyncio.create_task(self._initialize())

    async def _initialize(self):
        """Асинхронная инициализация"""
        await self.bot.wait_until_ready()
        await self.db.init()
        self.ready = True
        
        # Загружаем ID ветки из базы данных
        result = await self.db.fetch_one(
            "SELECT thread_id FROM games WHERE game_type = 'words' AND forum_id = ?",
            str(self.forum_channel_id)
        )
        if result and result['thread_id']:
            self.words_thread_id = int(result['thread_id'])
            
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
            if self.words_thread_id:
                thread = self.bot.get_channel(self.words_thread_id)
                if thread and not thread.archived:  # Проверяем что ветка существует и не архивирована
                    return  # Ветка существует и доступна
                
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
            
            # Сохраняем ID ветки в базу данных
            await self.db.execute(
                """
                INSERT INTO games (channel_id, game_type, forum_id, thread_id, created_at, updated_at)
                VALUES (?, 'words', ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT(channel_id) DO UPDATE SET 
                thread_id = ?, updated_at = CURRENT_TIMESTAMP
                """,
                str(thread.thread.id), str(self.forum_channel_id), str(thread.thread.id),
                str(thread.thread.id)
            )
            
            print(f"✅ Создана новая ветка для игры в слова: {thread.thread.id}")

        except Exception as e:
            print(f"❌ Ошибка при проверке/создании ветки для игры в слова: {e}")

    def is_valid_word(self, word: str) -> bool:
        """Проверка валидности слова"""
        # Только буквы русского алфавита
        return bool(re.match(r'^[а-яёА-ЯЁ]+$', word))

    async def get_last_word(self, channel_id: int) -> str:
        """Получение последнего слова из базы данных"""
        try:
            result = await self.db.fetch_one(
                "SELECT last_value FROM games WHERE channel_id = ? AND game_type = 'words'",
                str(channel_id)
            )
            return result['last_value'] if result and result['last_value'] else ""
        except Exception as e:
            print(f"❌ Ошибка при получении последнего слова: {e}")
            return ""

    async def get_used_words(self, channel_id: int) -> set:
        """Получение использованных слов из базы данных"""
        try:
            result = await self.db.fetch_one(
                "SELECT used_values FROM games WHERE channel_id = ? AND game_type = 'words'",
                str(channel_id)
            )
            if result and result['used_values']:
                try:
                    return set(json.loads(result['used_values']))
                except json.JSONDecodeError:
                    print("❌ Ошибка при декодировании JSON")
                    return set()
            return set()
        except Exception as e:
            print(f"❌ Ошибка при получении использованных слов: {e}")
            return set()

    async def save_word(self, channel_id: int, word: str):
        """Сохранение слова в базу данных"""
        try:
            # Получаем текущие использованные слова
            used_words = await self.get_used_words(channel_id)
            used_words.add(word.lower())

            # Обновляем или создаем запись в базе данных
            await self.db.execute(
                """INSERT INTO games (channel_id, game_type, last_value, used_values, updated_at) 
                   VALUES (?, 'words', ?, ?, CURRENT_TIMESTAMP)
                   ON CONFLICT(channel_id) DO UPDATE SET 
                   last_value = ?, used_values = ?, updated_at = CURRENT_TIMESTAMP""",
                str(channel_id), word, json.dumps(list(used_words)),
                word, json.dumps(list(used_words))
            )

            # Добавляем слово в словарь, если его там нет
            await self.db.execute(
                """INSERT OR IGNORE INTO words (word, language, part_of_speech) 
                   VALUES (?, 'ru', 'noun')""",
                word.lower()
            )

        except Exception as e:
            print(f"❌ Ошибка при сохранении слова: {e}")

    async def update_words_embed(self, channel_id: int):
        """Обновление эмбеда с текущей статистикой игры"""
        try:
            channel = self.bot.get_channel(channel_id)
            if channel:
                last_word = await self.get_last_word(channel_id)
                used_words = await self.get_used_words(channel_id)

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
                                          f"{Emojis.DOT} Последнее слово: `{last_word}`\n"
                                          f"{Emojis.DOT} Следующее слово должно начинаться на: `{last_word[-1].upper() if last_word else 'Любая буква'}`\n"
                                          f"{Emojis.DOT} Использовано слов: `{len(used_words)}`",
                                color="DEFAULT"
                            )
                            await message.edit(embed=new_embed)
                            return
        except Exception as e:
            print(f"❌ Ошибка при обновлении эмбеда: {e}")

    async def is_word_exists(self, word: str) -> bool:
        """Проверка существования слова в словаре"""
        try:
            result = await self.db.fetch_one(
                "SELECT COUNT(*) FROM words WHERE word = ? AND language = 'ru' AND part_of_speech = 'noun'",
                word.lower()
            )
            return bool(result)
        except Exception as e:
            print(f"❌ Ошибка при проверке слова: {e}")
            return True  # В случае ошибки разрешаем слово

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Обработчик сообщений для игры в слова"""
        if message.author.bot or not isinstance(message.channel, discord.Thread):
            return
            
        if message.channel.id != self.words_thread_id:
            return
            
        word = message.content.lower().strip()
        if not self.is_valid_word(word):
            return
            
        try:
            last_word = await self.get_last_word(message.channel.id)
            used_words = await self.get_used_words(message.channel.id)
            
            if last_word:  # Проверяем что last_word не пустой
                if word[0] != last_word[-1]:
                    await message.reply(
                        f"❌ Слово должно начинаться на букву **{last_word[-1]}**!",
                        delete_after=5
                    )
                    return
                    
            if word in used_words:
                await message.reply(
                    "❌ Это слово уже было использовано!",
                    delete_after=5
                )
                return
                
            # Сохраняем слово
            await self.save_word(message.channel.id, word)
            
        except Exception as e:
            print(f"❌ Ошибка в событии on_message: {e}")

async def setup(bot):
    await bot.add_cog(Words(bot)) 