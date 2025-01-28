import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.music import Music
from Niludetsu.utils import create_embed
import random

class Shuffle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.music = Music(bot)

    @app_commands.command(name="shuffle", description="Перемешать очередь воспроизведения")
    async def shuffle(self, interaction: discord.Interaction):
        """Перемешать треки в очереди воспроизведения"""
        player = await self.music.ensure_voice(interaction)
        if not player:
            return

        if not player.queue:
            await interaction.response.send_message(
                embed=create_embed(
                    description="❌ Очередь воспроизведения пуста!"
                ),
                ephemeral=True
            )
            return

        # Перемешиваем очередь
        tracks = list(player.queue)
        random.shuffle(tracks)
        player.queue.clear()
        for track in tracks:
            await player.queue.put_wait(track)

        await interaction.response.send_message(
            embed=create_embed(
                description="🔀 Очередь воспроизведения перемешана"
            )
        )

async def setup(bot):
    await bot.add_cog(Shuffle(bot)) 