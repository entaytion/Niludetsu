import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.utils.embed import create_embed

class CrashError(Exception):
    """Специальная ошибка для тестирования"""
    pass

class Crash(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="crash", description="Создать тестовую ошибку для проверки логирования")
    async def crash(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            embed=create_embed(
                description="🔨 Создаю тестовую ошибку...",
                color="RED"
            )
        )
        raise CrashError("Это тестовая ошибка для проверки системы логирования!")

async def setup(bot):
    await bot.add_cog(Crash(bot)) 