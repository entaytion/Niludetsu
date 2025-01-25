import discord
from discord import app_commands
from discord.ext import commands
import random
from utils import create_embed, EMOJIS

class Rand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="rand", description="Генерация случайного числа")
    @app_commands.describe(
        max="Максимальное число (или единственное число для диапазона 0-max)",
        min="Минимальное число (необязательно)"
    )
    async def rand(
        self, 
        interaction: discord.Interaction, 
        max: int,
        min: int = None
    ):
        try:
            if min is not None:
                # Если указаны оба параметра
                if min >= max:
                    raise ValueError("Минимальное число должно быть меньше максимального")
                result = random.randint(min, max)
                range_text = f"от {min} до {max}"
            else:
                # Если указан только один параметр
                if max <= 0:
                    raise ValueError("Число должно быть больше 0")
                result = random.randint(0, max)
                range_text = f"от 0 до {max}"

            embed = create_embed(
                title="🎲 Случайное число",
                description=f"В диапазоне {range_text}"
            )
            embed.add_field(
                name="Результат:",
                value=f"```{result}```",
                inline=False
            )
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(
                embed=create_embed(
                    description=f"{EMOJIS['ERROR']} Ошибка: {str(e)}"
                ),
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Rand(bot)) 