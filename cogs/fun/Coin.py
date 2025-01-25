import discord
from discord import app_commands
from discord.ext import commands
import random

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
        embed = discord.Embed(
            title="🪙 Подбрасываю монетку...",
            color=0x2F3136
        )

        # Добавляем анимацию подбрасывания
        await interaction.response.send_message(embed=embed)
        await interaction.edit_original_response(
            embed=discord.Embed(
                title="🪙 Монетка подброшена!",
                description=f"**Выпало:** {result}",
                color=0x2F3136
            )
        )

        # Если была попытка угадать
        if guess:
            # Добавляем информацию об угадывании через 1 секунду
            await interaction.edit_original_response(
                embed=discord.Embed(
                    title="🪙 Монетка подброшена!",
                    description=(
                        f"**Выпало:** {result}\n"
                        f"**Ваша догадка:** {guess}\n\n"
                        f"**Результат:** {'🎉 Вы угадали!' if guess == result else '😔 Вы не угадали'}"
                    ),
                    color=0x2F3136 if guess != result else 0x57F287
                )
            )

async def setup(bot):
    await bot.add_cog(Coin(bot)) 