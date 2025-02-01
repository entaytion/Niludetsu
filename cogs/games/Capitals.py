import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.utils.embed import Embed
import random
import asyncio

CAPITALS = {
    "Украина": "Киев",
    "Польша": "Варшава",
    "Швеция": "Стокгольм",
    "Норвегия": "Осло",
    "Финляндия": "Хельсинки",
    "Португалия": "Лиссабон",
    "Греция": "Афины",
    "Турция": "Анкара",
    "Египет": "Каир",
    "Казахстан": "Нур-Султан",
    "Россия": "Москва",
    "США": "Вашингтон",
    "Китай": "Пекин",
    "Япония": "Токио",
    "Германия": "Берлин",
    "Франция": "Париж",
    "Великобритания": "Лондон",
    "Италия": "Рим",
    "Канада": "Оттава",
    "Австралия": "Канберра",
    "Бразилия": "Бразилиа",
    "Индия": "Нью-Дели",
    "Испания": "Мадрид",
    "Мексика": "Мехико",
    "Южная Корея": "Сеул"
}

class CapitalsGame:
    def __init__(self):
        self.is_active = False
        self.channel_id = None
        self.current_country = None
        self.attempts = []
        self.max_attempts = 5
        
    def start_game(self, channel_id):
        if self.is_active:
            return False
        self.is_active = True
        self.channel_id = channel_id
        self.current_country = random.choice(list(CAPITALS.keys()))
        self.attempts = []
        return True
        
    def stop_game(self):
        self.is_active = False
        self.channel_id = None
        self.current_country = None
        self.attempts = []
        
    def check_answer(self, answer: str) -> bool:
        return answer.lower().strip() == CAPITALS[self.current_country].lower()
    
    def get_hint(self, guess):
        correct = CAPITALS[self.current_country].lower()
        guess = guess.lower().strip()
        
        if guess == correct:
            return "🟩" * len(guess)
        
        result = []
        for i, letter in enumerate(guess):
            if i < len(correct) and letter == correct[i]:
                result.append("🟩")  # Правильная буква в правильном месте
            elif letter in correct:
                result.append("🟨")  # Правильная буква в неправильном месте
            else:
                result.append("⬛")  # Неправильная буква
        
        return "".join(result)

class Capitals(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.games = {}
        
    def get_game(self, guild_id: int) -> CapitalsGame:
        if guild_id not in self.games:
            self.games[guild_id] = CapitalsGame()
        return self.games[guild_id]

    @app_commands.command(name="capitals", description="Игра 'Угадай столицу'")
    async def capitals(self, interaction: discord.Interaction):
        game = self.get_game(interaction.guild_id)
        
        if game.is_active:
            await interaction.response.send_message(
                embed=Embed(
                    description="Игра уже идет в этом канале!",
                    color="RED"
                ),
                ephemeral=True
            )
            return
            
        if game.start_game(interaction.channel_id):
            embed=Embed(
                title="🏛️ Угадай столицу",
                description=(
                    f"Я загадал столицу страны **{game.current_country}**\n"
                    f"У вас есть **{game.max_attempts}** попыток, чтобы угадать её.\n\n"
                    "• Пишите названия столиц в чат\n"
                    "• 🟩 - правильная буква в правильном месте\n"
                    "• 🟨 - правильная буква в неправильном месте\n"
                    "• ⬛ - неправильная буква"
                ),
                color="BLUE"
            )
            await interaction.response.send_message(embed=embed)
            
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
            
        game = self.get_game(message.guild.id)
        if not game.is_active or message.channel.id != game.channel_id:
            return
            
        guess = message.content.strip()
        game.attempts.append(guess)
        
        if game.check_answer(guess):
            embed=Embed(
                title="🎉 Поздравляем!",
                description=(
                    f"Вы угадали! Это действительно **{CAPITALS[game.current_country]}**\n"
                    f"Количество попыток: **{len(game.attempts)}**"
                ),
                color="GREEN"
            )
            game.stop_game()
            await message.reply(embed=embed)
        else:
            hint = game.get_hint(guess)
            attempts_left = game.max_attempts - len(game.attempts)
            
            if attempts_left == 0:
                embed=Embed(
                    title="❌ Игра окончена!",
                    description=(
                        f"К сожалению, вы не угадали. Это была столица **{CAPITALS[game.current_country]}**\n"
                        f"Ваши попытки:\n" + "\n".join(f"{i+1}. {attempt} {game.get_hint(attempt)}" 
                        for i, attempt in enumerate(game.attempts))
                    ),
                    color="RED"
                )
                game.stop_game()
            else:
                embed=Embed(
                    description=(
                        f"{hint}\n"
                        f"Осталось попыток: **{attempts_left}**"
                    ),
                    color="BLUE"
                )
            
            await message.reply(embed=embed)

async def setup(bot):
    await bot.add_cog(Capitals(bot)) 