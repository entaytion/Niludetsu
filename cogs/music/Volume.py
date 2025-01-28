import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.music import Music
from Niludetsu.utils import create_embed

class Volume(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.music = Music(bot)

    @app_commands.command(name="volume", description="Изменить громкость")
    @app_commands.describe(volume="Громкость от 0 до 100")
    async def volume(self, interaction: discord.Interaction, volume: int):
        """Изменить громкость воспроизведения"""
        if not 0 <= volume <= 100:
            await interaction.response.send_message(
                embed=create_embed(
                    description="❌ Громкость должна быть от 0 до 100!"
                ),
                ephemeral=True
            )
            return

        player = await self.music.ensure_voice(interaction)
        if not player:
            return

        await player.set_volume(volume)
        await interaction.response.send_message(
            embed=create_embed(
                description=f"🔊 Громкость установлена на {volume}%"
            )
        )

async def setup(bot):
    await bot.add_cog(Volume(bot)) 