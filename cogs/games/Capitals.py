import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.utils.embed import create_embed
import random

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
        self.countries = list(CAPITALS.keys())
        self.current_country = None
        self.score = 0
        self.total_questions = 5
        self.current_question = 0
        self.next_question()
        
    def next_question(self):
        if self.current_question < self.total_questions:
            self.current_country = random.choice(self.countries)
            self.countries.remove(self.current_country)
            self.current_question += 1
            return True
        return False
        
    def check_answer(self, answer: str) -> bool:
        return answer.lower().strip() == CAPITALS[self.current_country].lower()

class CapitalsView(discord.ui.View):
    def __init__(self, game: CapitalsGame):
        super().__init__()
        self.game = game
        self.add_item(CapitalsInput())
        
class CapitalsInput(discord.ui.TextInput):
    def __init__(self):
        super().__init__(
            label="Введите столицу",
            placeholder="Например: Париж",
            style=discord.TextStyle.short,
            required=True,
            max_length=50
        )
        
    async def callback(self, interaction: discord.Interaction):
        view: CapitalsView = self.view
        game = view.game
        
        is_correct = game.check_answer(self.value)
        if is_correct:
            game.score += 1
            color = "GREEN"
            result = "✅ Правильно!"
        else:
            color = "RED"
            result = f"❌ Неправильно! Правильный ответ: **{CAPITALS[game.current_country]}**"
            
        if game.next_question():
            embed = create_embed(
                title="🏛️ Угадай столицу",
                description=f"{result}\n\n"
                          f"**Счёт:** {game.score}/{game.current_question}\n"
                          f"**Следующий вопрос ({game.current_question}/{game.total_questions}):**\n"
                          f"Какая столица у страны **{game.current_country}**?",
                color=color
            )
            view = CapitalsView(game)
            await interaction.response.edit_message(embed=embed, view=view)
        else:
            embed = create_embed(
                title="🏛️ Игра окончена!",
                description=f"{result}\n\n"
                          f"**Итоговый счёт:** {game.score}/{game.total_questions}",
                color="BLUE"
            )
            await interaction.response.edit_message(embed=embed, view=None)

class Capitals(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="capitals", description="Игра 'Угадай столицу'")
    async def capitals(self, interaction: discord.Interaction):
        game = CapitalsGame()
        view = CapitalsView(game)
        
        await interaction.response.send_message(
            embed=create_embed(
                title="🏛️ Угадай столицу",
                description=f"**Вопрос {game.current_question}/{game.total_questions}:**\n"
                          f"Какая столица у страны **{game.current_country}**?",
                color="BLUE"
            ),
            view=view
        )

async def setup(bot):
    await bot.add_cog(Capitals(bot)) 