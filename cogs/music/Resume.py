import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.music import Music
from Niludetsu.utils import create_embed

class Resume(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.music = Music(bot)

    @app_commands.command(name="resume", description="Возобновить воспроизведение")
    async def resume(self, interaction: discord.Interaction):
        """Возобновить воспроизведение"""
        player = await self.music.ensure_voice(interaction)
        if not player:
            return

        if not player.paused:
            await interaction.response.send_message(
                embed=create_embed(
                    description="❌ Воспроизведение не приостановлено!"
                ),
                ephemeral=True
            )
            return

        await player.pause(False)
        await interaction.response.send_message(
            embed=create_embed(
                description="▶️ Воспроизведение возобновлено"
            )
        )

async def setup(bot):
    await bot.add_cog(Resume(bot)) 