import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, Modal, TextInput
import random
import json
import asyncio
from utils import create_embed

# База данных стран и их флагов
COUNTRIES = {
    "Украина": "https://flagcdn.com/w640/ua.png",
    "Франция": "https://flagcdn.com/w640/fr.png",
    "Германия": "https://flagcdn.com/w640/de.png",
    "Италия": "https://flagcdn.com/w640/it.png",
    "Испания": "https://flagcdn.com/w640/es.png",
    "Великобритания": "https://flagcdn.com/w640/gb.png",
    "Польша": "https://flagcdn.com/w640/pl.png",
    "Чехия": "https://flagcdn.com/w640/cz.png",
    "Австрия": "https://flagcdn.com/w640/at.png",
    "Венгрия": "https://flagcdn.com/w640/hu.png",
    "Греция": "https://flagcdn.com/w640/gr.png",
    "Португалия": "https://flagcdn.com/w640/pt.png",
    "Нидерланды": "https://flagcdn.com/w640/nl.png",
    "Бельгия": "https://flagcdn.com/w640/be.png",
    "Швеция": "https://flagcdn.com/w640/se.png",
    "Норвегия": "https://flagcdn.com/w640/no.png",
    "Финляндия": "https://flagcdn.com/w640/fi.png",
    "Дания": "https://flagcdn.com/w640/dk.png",
    "Ирландия": "https://flagcdn.com/w640/ie.png",
    "Швейцария": "https://flagcdn.com/w640/ch.png"
}

class GuessModal(Modal):
    def __init__(self):
        super().__init__(title="Угадай страну")
        self.guess = TextInput(
            label="Введите название страны",
            placeholder="Например: Франция",
            style=discord.TextStyle.short,
            required=True,
            max_length=50
        )
        self.add_item(self.guess)

    async def on_submit(self, interaction: discord.Interaction):
        game_view = self.view
        await game_view.process_guess(interaction, self.guess.value)

class CountryGame:
    def __init__(self):
        self.target_country = random.choice(list(COUNTRIES.keys()))
        self.flag_url = COUNTRIES[self.target_country]
        self.attempts = []
        self.max_attempts = 7
        self.game_over = False
        
    def make_guess(self, guess):
        guess = guess.strip().capitalize()
        self.attempts.append(guess)
        
        if guess == self.target_country:
            self.game_over = True
            return True
            
        return False
        
    def get_hint(self, guess):
        if guess == self.target_country:
            return "🟩" * len(guess)
            
        hint = ""
        target_chars = set(self.target_country.lower())
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

class CountryView(View):
    def __init__(self, game):
        super().__init__(timeout=300)  # 5 минут на игру
        self.game = game
        
    @discord.ui.button(label="Сделать предположение", style=discord.ButtonStyle.primary)
    async def guess(self, interaction: discord.Interaction, button: Button):
        if len(self.game.attempts) >= self.game.max_attempts:
            await interaction.response.send_message("❌ Игра окончена! У вас закончились попытки.", ephemeral=True)
            return
            
        modal = GuessModal()
        modal.view = self
        await interaction.response.send_modal(modal)
        
    async def process_guess(self, interaction: discord.Interaction, guess):
        is_correct = self.game.make_guess(guess)
        
        if is_correct:
            embed = create_embed(
                title="🎮 Поздравляем!",
                description=f"✅ Вы угадали страну: **{self.game.target_country}**!\n"
                           f"Количество попыток: **{len(self.game.attempts)}**\n\n"
                           f"**История попыток:**\n{self.game.get_status()}"
            )
            embed.set_image(url=self.game.flag_url)
            self.stop()
            await interaction.response.edit_message(embed=embed, view=None)
            return
            
        if len(self.game.attempts) >= self.game.max_attempts:
            embed = create_embed(
                title="❌ Игра окончена!",
                description=f"У вас закончились попытки!\n"
                           f"Правильный ответ: **{self.game.target_country}**\n\n"
                           f"**История попыток:**\n{self.game.get_status()}"
            )
            embed.set_image(url=self.game.flag_url)
            self.stop()
            await interaction.response.edit_message(embed=embed, view=None)
            return
            
        embed = create_embed(
            title="🎮 Угадай страну",
            description=f"Осталось попыток: **{self.game.max_attempts - len(self.game.attempts)}**\n\n"
                       f"**История попыток:**\n{self.game.get_status()}\n\n"
                       "Нажмите кнопку ниже, чтобы сделать следующее предположение!"
        )
        embed.set_image(url=self.game.flag_url)
        await interaction.response.edit_message(embed=embed, view=self)

class Country(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @app_commands.command(name="country", description="Начать игру 'Угадай страну по флагу'")
    async def country(self, interaction: discord.Interaction):
        game = CountryGame()
        
        embed = create_embed(
            title="🎮 Угадай страну",
            description=f"У вас есть **{game.max_attempts}** попыток, чтобы угадать страну по флагу.\n"
                       "После каждой попытки вы получите подсказку в виде общих букв.\n\n"
                       "Нажмите кнопку ниже, чтобы сделать предположение!"
        )
        embed.set_image(url=game.flag_url)
        
        view = CountryView(game)
        await interaction.response.send_message(embed=embed, view=view)
        
        await view.wait()
        if not view.is_finished():
            embed = create_embed(
                title="⏰ Время вышло!",
                description=f"Правильный ответ: **{game.target_country}**\n\n"
                           f"**История попыток:**\n{game.get_status()}"
            )
            embed.set_image(url=game.flag_url)
            await interaction.edit_original_message(embed=embed, view=None)

async def setup(bot):
    await bot.add_cog(Country(bot)) 