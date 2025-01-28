import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.music import Music
from Niludetsu.utils import create_embed

class Leave(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.music = Music(bot)

    @app_commands.command(name="leave", description="Отключиться от голосового канала")
    async def leave(self, interaction: discord.Interaction):
        """Отключиться от голосового канала"""
        player = await self.music.ensure_voice(interaction)
        if not player:
            return

        await player.disconnect()
        await interaction.response.send_message(
            embed=create_embed(
                description="👋 Отключился от голосового канала"
            )
        )

async def setup(bot):
    await bot.add_cog(Leave(bot)) 