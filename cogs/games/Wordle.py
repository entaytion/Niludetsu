import discord
from discord.ext import commands
from discord import app_commands
from utils import create_embed
import random
import yaml

LETTERS = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
CORRECT = "🟩"  # Правильная буква на правильном месте
PRESENT = "🟨"  # Правильная буква на неправильном месте
ABSENT = "⬛"   # Буква отсутствует в слове

class WordleGame:
    def __init__(self, channel_id: int, message_id: int, word_length: int = 5):
        with open("config/config.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            words = config.get('words', {}).get(str(word_length), [])
            if not words:
                raise ValueError(f"Нет слов длины {word_length} в конфигурации")
            self.word = random.choice(words).upper()
        
        self.attempts = []
        self.max_attempts = 6
        self.is_won = False
        self.is_over = False
        self.channel_id = channel_id
        self.message_id = message_id
        self.word_length = word_length
        self.used_letters = {
            'correct': set(),    # Зеленые буквы
            'present': set(),    # Желтые буквы
            'absent': set()      # Отсутствующие буквы
        }

    def make_guess(self, guess: str) -> tuple[str, list[tuple[str, str]]]:
        """Проверяет попытку и возвращает результат"""
        guess = guess.upper()
        result = ""
        letters_with_styles = []
        word_letters = list(self.word)
        
        # Первый проход: находим точные совпадения
        for i, letter in enumerate(guess):
            if letter == word_letters[i]:
                result += CORRECT
                letters_with_styles.append((letter, "correct"))
                word_letters[i] = None
                self.used_letters['correct'].add(letter)
            else:
                result += "?"
                letters_with_styles.append((letter, "unknown"))

        # Второй проход: проверяем буквы на неправильных позициях
        for i, (letter, style) in enumerate(letters_with_styles):
            if style == "unknown":
                if letter in word_letters:
                    result = result[:i] + PRESENT + result[i+1:]
                    letters_with_styles[i] = (letter, "present")
                    word_letters[word_letters.index(letter)] = None
                    self.used_letters['present'].add(letter)
                else:
                    result = result[:i] + ABSENT + result[i+1:]
                    letters_with_styles[i] = (letter, "absent")
                    self.used_letters['absent'].add(letter)

        self.attempts.append((letters_with_styles, result))
        
        if guess == self.word:
            self.is_won = True
            self.is_over = True
        elif len(self.attempts) >= self.max_attempts:
            self.is_over = True

        return result, letters_with_styles

    def get_game_state(self) -> str:
        """Возвращает текущее состояние игры"""
        state = ""
        for letters_with_styles, result in self.attempts:
            # Добавляем строку с буквами
            for letter, style in letters_with_styles:
                state += f"[{letter}]"
            state += "  "
            # Добавляем строку с результатами
            state += result + "\n"
        return state

    def get_keyboard_state(self) -> str:
        """Возвращает состояние клавиатуры с использованными буквами"""
        keyboard = ""
        for letter in LETTERS:
            if letter in self.used_letters['correct']:
                keyboard += f"🟩[{letter}]"
            elif letter in self.used_letters['present']:
                keyboard += f"🟨[{letter}]"
            elif letter in self.used_letters['absent']:
                keyboard += f"⬛[{letter}]"
            else:
                keyboard += f"⬜[{letter}]"
            keyboard += " "
        return keyboard

class Wordle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_games = {}  # {channel_id: {user_id: game}}
        with open("config/config.yaml", "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
            self.available_lengths = [
                length for length in map(int, self.config.get('words', {}).keys())
                if self.config['words'].get(str(length))
            ]
            self.available_lengths.sort()

    @app_commands.command(name="wordle", description="Начать игру в Wordle")
    @app_commands.describe(word_length="Длина загаданного слова")
    async def wordle(self, interaction: discord.Interaction, word_length: int = 5):
        if word_length not in self.available_lengths:
            await interaction.response.send_message(
                embed=create_embed(
                    description=f"❌ Доступные длины слов: {', '.join(map(str, self.available_lengths))}"
                )
            )
            return

        channel_id = interaction.channel_id
        user_id = interaction.user.id

        # Проверяем есть ли активная игра у пользователя
        if channel_id in self.active_games and user_id in self.active_games[channel_id]:
            await interaction.response.send_message(
                embed=create_embed(
                    description="У вас уже есть активная игра!"
                )
            )
            return

        try:
            # Создаем сообщение с игрой
            message = await interaction.response.send_message(
                embed=create_embed(
                    title="🎯 Wordle",
                    description=(
                        f"**{interaction.user.mention} начал игру в Wordle!**\n\n"
                        f"Я загадал слово из {word_length} букв. У вас есть 6 попыток, чтобы угадать его!\n\n"
                        "🟩 - буква на правильном месте\n"
                        "🟨 - буква есть в слове, но не на этом месте\n"
                        "⬛ - такой буквы нет в слове\n\n"
                        "Просто напишите слово в чат для попытки.\n\n"
                        "Доступные буквы:\n" +
                        " ".join(f"⬜[{letter}]" for letter in LETTERS)
                    )
                )
            )
            message = await interaction.original_response()

            # Создаем новую игру
            game = WordleGame(channel_id, message.id, word_length)
            
            # Сохраняем игру
            if channel_id not in self.active_games:
                self.active_games[channel_id] = {}
            self.active_games[channel_id][user_id] = game
        except ValueError as e:
            await interaction.response.send_message(
                embed=create_embed(
                    description=f"❌ {str(e)}"
                )
            )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Игнорируем сообщения от ботов
        if message.author.bot:
            return

        channel_id = message.channel.id
        user_id = message.author.id

        # Проверяем есть ли активная игра в этом канале для этого пользователя
        if channel_id not in self.active_games or user_id not in self.active_games[channel_id]:
            return

        game = self.active_games[channel_id][user_id]
        word = message.content.lower()

        # Проверяем правильной ли длины слово
        if len(word) != game.word_length:
            return

        # Проверяем все ли буквы кириллицей
        if not all(letter in LETTERS.lower() for letter in word):
            return

        # Удаляем сообщение пользователя для чистоты чата
        try:
            await message.delete()
        except:
            pass

        result, letters_with_styles = game.make_guess(word)
        game_state = game.get_game_state()
        keyboard_state = game.get_keyboard_state()
        
        description = (
            f"**{message.author.mention} играет в Wordle!**\n\n"
            f"Попытка {len(game.attempts)}/6:\n"
            f"```\n{game_state}```\n"
            f"Использованные буквы:\n{keyboard_state}\n"
        )
        
        if game.is_won:
            description += f"\n🎉 **Поздравляем! Вы угадали слово `{game.word}`!**"
            del self.active_games[channel_id][user_id]
            if not self.active_games[channel_id]:
                del self.active_games[channel_id]
        elif game.is_over:
            description += f"\n❌ **Игра окончена! Загаданное слово: `{game.word}`**"
            del self.active_games[channel_id][user_id]
            if not self.active_games[channel_id]:
                del self.active_games[channel_id]

        # Обновляем оригинальное сообщение с игрой
        try:
            channel = message.channel
            game_message = await channel.fetch_message(game.message_id)
            await game_message.edit(
                embed=create_embed(
                    title="🎯 Wordle",
                    description=description
                )
            )
        except:
            pass

async def setup(bot):
    await bot.add_cog(Wordle(bot))