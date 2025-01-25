import discord
from discord import app_commands
from discord.ext import commands
import random
from utils import create_embed, EMOJIS

class Coin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="coin", description="Подбросить монетку")
    @app_commands.describe(guess="Ваша догадка: орёл или решка")
    @app_commands.choices(guess=[
        app_commands.Choice(name="Орёл", value="орёл"),
        app_commands.Choice(name="Решка", value="решка")
    ])
    async def coin(
        self,
        interaction: discord.Interaction,
        guess: str = None
    ):
        # Подбрасываем монетку
        result = random.choice(["орёл", "решка"])
        
        # Создаем embed сообщение
        embed = create_embed(
            title="🪙 Подбрасываю монетку..."
        )

        # Добавляем анимацию подбрасывания
        await interaction.response.send_message(embed=embed)
        await interaction.edit_original_response(
            embed=create_embed(
                title="🪙 Монетка подброшена!",
                description=f"**Выпало:** {result}"
            )
        )

        # Если была попытка угадать
        if guess:
            # Добавляем информацию об угадывании через 1 секунду
            await interaction.edit_original_response(
                embed=create_embed(
                    title="🪙 Монетка подброшена!",
                    description=(
                        f"**Выпало:** {result}\n"
                        f"**Ваша догадка:** {guess}\n\n"
                        f"**Результат:** {EMOJIS['SUCCESS'] + ' Вы угадали!' if guess == result else EMOJIS['ERROR'] + ' Вы не угадали'}"
                    ),
                    color=0x57F287 if guess == result else None
                )
            )

async def setup(bot):
    await bot.add_cog(Coin(bot))