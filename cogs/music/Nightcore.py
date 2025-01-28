import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.music import Music
from Niludetsu.utils import create_embed

class Nightcore(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.music = Music(bot)

    @app_commands.command(name="nightcore", description="Включить/выключить эффект Nightcore")
    async def nightcore(self, interaction: discord.Interaction):
        """Включить или выключить эффект Nightcore"""
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
            # Переключаем эффект Nightcore
            if not hasattr(player, 'nightcore'):
                player.nightcore = False
            
            player.nightcore = not player.nightcore
            
            # Применяем эффект
            filters = player.filters
            if player.nightcore:
                filters.timescale.set(speed=1.2, pitch=1.2, rate=1.0)
                await player.set_filters(filters)
                status = "включен"
                emoji = "🎵"
            else:
                filters.reset()
                await player.set_filters(filters)
                status = "выключен"
                emoji = "🎶"

            await interaction.followup.send(
                embed=create_embed(
                    description=f"{emoji} Эффект Nightcore {status}"
                )
            )
        except Exception as e:
            print(f"Error applying nightcore effect: {e}")
            await interaction.followup.send(
                embed=create_embed(
                    description="❌ Произошла ошибка при применении эффекта!"
                ),
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Nightcore(bot)) 