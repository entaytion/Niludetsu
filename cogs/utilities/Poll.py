import discord
from discord.ext import commands
from discord import app_commands
from utils import create_embed

EMOJI_NUMBERS = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']

class Poll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="poll", description="Создать опрос с вариантами ответов")
    @app_commands.describe(
        question="Вопрос для опроса",
        option1="Вариант 1",
        option2="Вариант 2",
        option3="Вариант 3 (необязательно)",
        option4="Вариант 4 (необязательно)",
        option5="Вариант 5 (необязательно)"
    )
    async def poll(
        self, 
        interaction: discord.Interaction, 
        question: str,
        option1: str,
        option2: str,
        option3: str = None,
        option4: str = None,
        option5: str = None
    ):
        await interaction.response.defer()

        try:
            # Собираем все не-None опции
            options = [opt for opt in [option1, option2, option3, option4, option5] if opt is not None]
            
            if len(options) < 2:
                await interaction.followup.send(
                    embed=create_embed(
                        description="Нужно указать минимум 2 варианта ответа!"
                    )
                )
                return

            # Создаем описание опроса с эмодзи
            description = f"**{question}**\n\n"
            for i, option in enumerate(options):
                description += f"{EMOJI_NUMBERS[i]} {option}\n"

            # Создаем эмбед
            embed = create_embed(
                title="📊 Опрос",
                description=description,
                footer={"text": f"Создал: {interaction.user.name}"}
            )

            # Отправляем сообщение и получаем его объект
            message = await interaction.followup.send(embed=embed)

            # Добавляем реакции
            for i in range(len(options)):
                await message.add_reaction(EMOJI_NUMBERS[i])

        except Exception as e:
            await interaction.followup.send(
                embed=create_embed(
                    description=f"Произошла ошибка при создании опроса: {str(e)}"
                )
            )

async def setup(bot):
    await bot.add_cog(Poll(bot))
