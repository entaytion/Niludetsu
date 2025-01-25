import discord
from discord import app_commands
from discord.ext import commands
import random
from utils import create_embed, EMOJIS

class Magic8Ball(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.answers = {
            'positive': [
                "Да, определенно ✨",
                "Можешь быть уверен в этом 👍",
                "Безусловно да ⭐",
                "Весьма вероятно 🌟",
                "Знаки говорят — да ✅",
                "Мне кажется — да 💫"
            ],
            'neutral': [
                "Пока не ясно 🤔",
                "Спроси позже ⏳",
                "Лучше не рассказывать 🤐",
                "Сейчас нельзя предсказать 🎲",
                "Сконцентрируйся и спроси опять 🔮"
            ],
            'negative': [
                "Даже не думай ❌",
                "Мой ответ — нет 🚫",
                "Весьма сомнительно ⛔",
                "Определенно нет ❎",
                "Перспективы не очень хорошие 🌧️"
            ]
        }

    @app_commands.command(name="8ball", description="Магический шар ответит на твой вопрос")
    @app_commands.describe(question="Задай свой вопрос магическому шару")
    async def magic_8ball(self, interaction: discord.Interaction, question: str):
        if not question.endswith('?'):
            await interaction.response.send_message(
                embed=create_embed(
                    description=f"{EMOJIS['ERROR']} Это не похоже на вопрос! Добавь знак вопроса в конце."
                )
            )
            return

        # Выбираем категорию ответа
        category = random.choice(['positive', 'neutral', 'negative'])
        answer = random.choice(self.answers[category])

        # Создаем цвет в зависимости от категории
        colors = {
            'positive': 0x2ECC71,  # Зеленый
            'neutral': 0xF1C40F,   # Желтый
            'negative': 0xE74C3C   # Красный
        }

        embed = create_embed(
            title="🎱 Магический шар",
            fields=[
                {"name": "Вопрос:", "value": question, "inline": False},
                {"name": "Ответ:", "value": answer, "inline": False}
            ],
            color=colors[category]
        )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Magic8Ball(bot)) 