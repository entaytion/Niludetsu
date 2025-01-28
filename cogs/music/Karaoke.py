import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.music import Music
from Niludetsu.utils import create_embed

class Karaoke(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.music = Music(bot)

    @app_commands.command(name="karaoke", description="Включить/выключить режим караоке")
    async def karaoke(self, interaction: discord.Interaction):
        """Включить или выключить режим караоке (подавление вокала)"""
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
            # Переключаем режим караоке
            if not hasattr(player, 'karaoke_enabled'):
                player.karaoke_enabled = False
            
            player.karaoke_enabled = not player.karaoke_enabled
            
            # Применяем эффект
            filters = player.filters
            if player.karaoke_enabled:
                filters.karaoke.set(
                    level=1.0,
                    mono_level=1.0,
                    filter_band=220.0,
                    filter_width=100.0
                )
                await player.set_filters(filters)
                status = "включен"
                emoji = "🎤"
            else:
                filters.reset()
                await player.set_filters(filters)
                status = "выключен"
                emoji = "🎵"

            await interaction.followup.send(
                embed=create_embed(
                    description=f"{emoji} Режим караоке {status}"
                )
            )
        except Exception as e:
            print(f"Error applying karaoke effect: {e}")
            await interaction.followup.send(
                embed=create_embed(
                    description="❌ Произошла ошибка при применении эффекта!"
                ),
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Karaoke(bot)) 