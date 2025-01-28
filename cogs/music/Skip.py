import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.music import Music
from Niludetsu.utils import create_embed

class Skip(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.music = Music(bot)

    @app_commands.command(name="skip", description="Пропустить текущий трек")
    async def skip(self, interaction: discord.Interaction):
        """Пропустить текущий трек"""
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

        # Проверяем, есть ли следующий трек
        if player.queue.is_empty:
            await player.stop()
            await interaction.followup.send(
                embed=create_embed(
                    description="⏭️ Трек пропущен! Очередь пуста."
                )
            )
            return

        # Получаем информацию о следующем треке
        next_track = player.queue.peek()
        
        # Пропускаем текущий трек
        await player.skip()
        
        await interaction.followup.send(
            embed=create_embed(
                title="⏭️ Трек пропущен",
                description=f"Следующий трек:\n**{next_track.title}**\nАвтор: {next_track.author}"
            )
        )

async def setup(bot):
    await bot.add_cog(Skip(bot)) 