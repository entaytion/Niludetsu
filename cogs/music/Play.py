import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.music import Music
from Niludetsu.utils.embed import Embed

class Play(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.music = Music(bot)

    @app_commands.command(name="play", description="Воспроизвести музыку")
    @app_commands.describe(query="Название песни или URL")
    async def play(self, interaction: discord.Interaction, query: str):
        """Воспроизвести музыку"""
        await self.music.play_song(interaction, query)

async def setup(bot):
    await bot.add_cog(Play(bot))