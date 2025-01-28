import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, TextInput
from Niludetsu.utils.embed import create_embed
import random

# База данных стран и их флагов
COUNTRIES = {
    "Украина": "https://flagcdn.com/w2560/ua.png",
    "Польша": "https://flagcdn.com/w2560/pl.png",
    "Швеция": "https://flagcdn.com/w2560/se.png",
    "Норвегия": "https://flagcdn.com/w2560/no.png",
    "Финляндия": "https://flagcdn.com/w2560/fi.png",
    "Португалия": "https://flagcdn.com/w2560/pt.png",
    "Греция": "https://flagcdn.com/w2560/gr.png",
    "Турция": "https://flagcdn.com/w2560/tr.png",
    "Египет": "https://flagcdn.com/w2560/eg.png",
    "Казахстан": "https://flagcdn.com/w2560/kz.png",
    "Россия": "https://flagcdn.com/w2560/ru.png",
    "США": "https://flagcdn.com/w2560/us.png",
    "Китай": "https://flagcdn.com/w2560/cn.png",
    "Япония": "https://flagcdn.com/w2560/jp.png",
    "Германия": "https://flagcdn.com/w2560/de.png",
    "Франция": "https://flagcdn.com/w2560/fr.png",
    "Великобритания": "https://flagcdn.com/w2560/gb.png",
    "Италия": "https://flagcdn.com/w2560/it.png",
    "Канада": "https://flagcdn.com/w2560/ca.png",
    "Австралия": "https://flagcdn.com/w2560/au.png",
    "Бразилия": "https://flagcdn.com/w2560/br.png",
    "Индия": "https://flagcdn.com/w2560/in.png",
    "Испания": "https://flagcdn.com/w2560/es.png",
    "Мексика": "https://flagcdn.com/w2560/mx.png",
    "Южная Корея": "https://flagcdn.com/w2560/kr.png"
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

class CountryView(discord.ui.View):
    def __init__(self, game: CountryGame):
        super().__init__()
        self.game = game
        
    @discord.ui.button(label="Угадать", style=discord.ButtonStyle.primary)
    async def guess(self, interaction: discord.Interaction, button: discord.ui.Button):
        if len(self.game.attempts) >= self.game.max_attempts:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Игра окончена! У вас закончились попытки.",
                    color="RED"
                ),
                ephemeral=True
            )
            return
            
        await interaction.response.send_modal(GuessModal())
        
    async def process_guess(self, interaction: discord.Interaction, guess: str):
        if not guess:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Пожалуйста, введите название страны!",
                    color="RED"
                ),
                ephemeral=True
            )
            return
            
        correct = self.game.make_guess(guess)
        attempts_left = self.game.max_attempts - len(self.game.attempts)
        
        if correct:
            embed = create_embed(
                title="🌍 Угадай страну",
                description=f"🎉 **Поздравляем! Вы угадали страну!**\n\n{self.game.get_status()}",
                image=self.game.flag_url,
                color="GREEN"
            )
            self.disable_all_items()
            await interaction.response.edit_message(embed=embed, view=self)
        elif attempts_left == 0:
            embed = create_embed(
                title="🌍 Угадай страну",
                description=f"❌ **Игра окончена!**\nПравильный ответ: **{self.game.target_country}**\n\n{self.game.get_status()}",
                image=self.game.flag_url,
                color="RED"
            )
            self.disable_all_items()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            embed = create_embed(
                title="🌍 Угадай страну",
                description=f"Осталось попыток: **{attempts_left}**\n\n{self.game.get_status()}",
                image=self.game.flag_url,
                color="BLUE"
            )
            await interaction.response.edit_message(embed=embed)
            
    def disable_all_items(self):
        for item in self.children:
            item.disabled = True

class Country(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="country", description="Игра 'Угадай страну по флагу'")
    async def country(self, interaction: discord.Interaction):
        game = CountryGame()
        view = CountryView(game)
        
        await interaction.response.send_message(
            embed=create_embed(
                title="🌍 Угадай страну",
                description=f"У вас есть **{game.max_attempts}** попыток, чтобы угадать страну по флагу.\nНажмите кнопку 'Угадать' для ввода ответа.",
                image=game.flag_url,
                color="BLUE"
            ),
            view=view
        )

async def setup(bot):
    await bot.add_cog(Country(bot)) 