import discord
from discord.ext import commands
import random
from Niludetsu.utils.embed import Embed

class Ball(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.responses = [
            "Бесспорно",
            "Предрешено",
            "Никаких сомнений",
            "Определённо да",
            "Можешь быть уверен в этом",
            "Мне кажется — да",
            "Вероятнее всего",
            "Хорошие перспективы",
            "Знаки говорят — да",
            "Да",
            "Пока не ясно, попробуй снова",
            "Спроси позже",
            "Лучше не рассказывать",
            "Сейчас нельзя предсказать",
            "Сконцентрируйся и спроси опять",
            "Даже не думай",
            "Мой ответ — нет",
            "По моим данным — нет",
            "Перспективы не очень хорошие",
            "Весьма сомнительно"
        ]

    @discord.app_commands.command(name="8ball", description="Магический шар ответит на ваш вопрос")
    @discord.app_commands.describe(question="Ваш вопрос")
    async def ball(self, interaction: discord.Interaction, question: str):
        response = random.choice(self.responses)
        
        await interaction.response.send_message(
            embed=Embed(
                title="🎱 Магический шар",
                description=f"**Вопрос:** {question}\n**Ответ:** {response}",
                color="BLUE"
            )
        )

async def setup(bot):
    await bot.add_cog(Ball(bot)) 