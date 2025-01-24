import discord
from discord.ext import commands
import wavelink
from utils import create_embed
from .Core import Core
import random

class Shuffle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.core = None
        
    async def cog_load(self):
        self.core = self.bot.get_cog('Core')

    @discord.app_commands.command(name="shuffle", description="Перемешать очередь треков")
    async def shuffle(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            player = await self.core.get_player(interaction)
            if not player or not player.connected:
                await interaction.followup.send(
                    embed=create_embed(
                        description="Я не подключен к голосовому каналу!"
                    )
                )
                return

            if not player.queue:
                await interaction.followup.send(
                    embed=create_embed(
                        description="Очередь пуста, нечего перемешивать!"
                    )
                )
                return

            queue_list = list(player.queue)
            random.shuffle(queue_list)
            player.queue.clear()
            for track in queue_list:
                player.queue.put(track)

            await interaction.followup.send(
                embed=create_embed(
                    description="Очередь треков перемешана."
                )
            )
        except Exception as e:
            print(f"Error in shuffle command: {e}")
            await interaction.followup.send(
                embed=create_embed(
                    description="Произошла ошибка!"
                )
            )

async def setup(bot):
    await bot.add_cog(Shuffle(bot)) 