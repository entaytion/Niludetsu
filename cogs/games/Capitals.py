import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, Modal, TextInput
import random
import json
import asyncio
from utils import create_embed

# База данных столиц и стран
CAPITALS = {
    "Москва": "Россия",
    "Париж": "Франция",
    "Берлин": "Германия",
    "Рим": "Италия",
    "Мадрид": "Испания",
    "Лондон": "Великобритания",
    "Варшава": "Польша",
    "Прага": "Чехия",
    "Вена": "Австрия",
    "Будапешт": "Венгрия",
    "Афины": "Греция",
    "Лиссабон": "Португалия",
    "Амстердам": "Нидерланды",
    "Брюссель": "Бельгия",
    "Стокгольм": "Швеция",
    "Осло": "Норвегия",
    "Хельсинки": "Финляндия",
    "Копенгаген": "Дания",
    "Дублин": "Ирландия",
    "Берн": "Швейцария"
}

class GuessModal(Modal):
    def __init__(self):
        super().__init__(title="Угадай столицу")
        self.guess = TextInput(
            label="Введите название столицы",
            placeholder="Например: Париж",
            style=discord.TextStyle.short,
            required=True,
            max_length=50
        )
        self.add_item(self.guess)

    async def on_submit(self, interaction: discord.Interaction):
        game_view = self.view
        await game_view.process_guess(interaction, self.guess.value)

class CapitalsGame:
    def __init__(self):
        self.target_capital = random.choice(list(CAPITALS.keys()))
        self.target_country = CAPITALS[self.target_capital]
        self.attempts = []
        self.max_attempts = 7
        self.game_over = False
        
    def make_guess(self, guess):
        guess = guess.strip().capitalize()
        self.attempts.append(guess)
        
        if guess == self.target_capital:
            self.game_over = True
            return True
            
        return False
        
    def get_hint(self, guess):
        if guess == self.target_capital:
            return "🟩" * len(guess)
            
        hint = ""
        target_chars = set(self.target_capital.lower())
        guess_chars = set(guess.lower())
        
        common_chars = target_chars & guess_chars
        if not common_chars:
            return "❌ Нет общих букв"
            
        return f"📝 Общие буквы: {', '.join(sorted(common_chars))}"
        
    def get_status(self):
        status = []
        for attempt in self.attempts:
            hint = self.get_hint(attempt)
            status.append(f"**Попытка {len(status) + 1}:** {attempt}\n{hint}")
        return "\n".join(status)

class CapitalsView(View):
    def __init__(self, game):
        super().__init__(timeout=300)  # 5 минут на игру
        self.game = game
        
    @discord.ui.button(label="Сделать предположение", style=discord.ButtonStyle.primary)
    async def guess(self, interaction: discord.Interaction, button: Button):
        if len(self.game.attempts) >= self.game.max_attempts:
            await interaction.response.send_message("❌ Игра окончена! У вас закончились попытки.")
            return
            
        modal = GuessModal()
        modal.view = self
        await interaction.response.send_modal(modal)
        
    async def process_guess(self, interaction: discord.Interaction, guess):
        is_correct = self.game.make_guess(guess)
        
        if is_correct:
            embed = create_embed(
                title="🎮 Поздравляем!",
                description=f"✅ Вы угадали столицу: **{self.game.target_capital}**!\n"
                           f"Это столица страны **{self.game.target_country}**\n"
                           f"Количество попыток: **{len(self.game.attempts)}**\n\n"
                           f"**История попыток:**\n{self.game.get_status()}"
            )
            self.stop()
            await interaction.response.edit_message(embed=embed, view=None)
            return
            
        if len(self.game.attempts) >= self.game.max_attempts:
            embed = create_embed(
                title="❌ Игра окончена!",
                description=f"У вас закончились попытки!\n"
                           f"Правильный ответ: **{self.game.target_capital}** ({self.game.target_country})\n\n"
                           f"**История попыток:**\n{self.game.get_status()}"
            )
            self.stop()
            await interaction.response.edit_message(embed=embed, view=None)
            return
            
        embed = create_embed(
            title="🎮 Угадай столицу",
            description=f"Угадайте столицу страны **{self.game.target_country}**\n"
                       f"Осталось попыток: **{self.game.max_attempts - len(self.game.attempts)}**\n\n"
                       f"**История попыток:**\n{self.game.get_status()}\n\n"
                       "Нажмите кнопку ниже, чтобы сделать следующее предположение!"
        )
        await interaction.response.edit_message(embed=embed, view=self)

class Capitals(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @app_commands.command(name="capitals", description="Начать игру 'Угадай столицу'")
    async def capitals(self, interaction: discord.Interaction):
        game = CapitalsGame()
        
        embed = create_embed(
            title="🎮 Угадай столицу",
            description=f"Угадайте столицу страны **{game.target_country}**\n"
                       f"У вас есть **{game.max_attempts}** попыток.\n"
                       "После каждой попытки вы получите подсказку в виде общих букв.\n\n"
                       "Нажмите кнопку ниже, чтобы сделать предположение!"
        )
        
        view = CapitalsView(game)
        await interaction.response.send_message(embed=embed, view=view)
        
        await view.wait()
        if not view.is_finished():
            embed = create_embed(
                title="⏰ Время вышло!",
                description=f"Правильный ответ: **{game.target_capital}** ({game.target_country})\n\n"
                           f"**История попыток:**\n{game.get_status()}"
            )
            await interaction.edit_original_message(embed=embed, view=None)

async def setup(bot):
    await bot.add_cog(Capitals(bot)) 