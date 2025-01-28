import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.music import Music
from Niludetsu.utils import create_embed

class Pause(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.music = Music(bot)

    @app_commands.command(name="pause", description="Поставить трек на паузу или снять с паузы")
    async def pause(self, interaction: discord.Interaction):
        """Поставить трек на паузу или снять с паузы"""
        await interaction.response.defer()

        player = await self.music.ensure_voice(interaction)
        if not player:
            return

        if not player.playing:
            await interaction.followup.send(
                embed=create_embed(
                    description="❌ Сейчас ничего не играет!"
                ),
                ephemeral=True
            )
            return

        try:
            # Переключаем состояние паузы
            is_paused = not player.paused
            await player.pause(is_paused)
            
            await interaction.followup.send(
                embed=create_embed(
                    description=f"{'⏸️ Трек поставлен на паузу' if is_paused else '▶️ Воспроизведение продолжено'}"
                )
            )
        except Exception as e:
            print(f"Error toggling pause: {e}")
            await interaction.followup.send(
                embed=create_embed(
                    description="❌ Произошла ошибка при попытке поставить на паузу!"
                ),
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Pause(bot)) 