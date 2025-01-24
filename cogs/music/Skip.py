import discord
from discord.ext import commands
import wavelink
from utils import create_embed
from .Core import Core

class Skip(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.core = None
        
    async def cog_load(self):
        self.core = self.bot.get_cog('Core')

    @discord.app_commands.command(name="skip", description="Пропустить текущий трек")
    async def skip(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            player = await self.core.get_player(interaction)
            if not player:
                await interaction.followup.send(
                    embed=create_embed(
                        description="Я не подключен к голосовому каналу!"
                    )
                )
                return

            if not player.current:
                await interaction.followup.send(
                    embed=create_embed(
                        description="Сейчас ничего не играет!"
                    )
                )
                return

            await player.stop()
            await interaction.followup.send(
                embed=create_embed(
                    description="Трек пропущен!"
                )
            )
            
        except Exception as e:
            print(f"Error in skip command: {e}")
            await interaction.followup.send(
                embed=create_embed(
                    description="Произошла ошибка при пропуске трека!"
                )
            )

async def setup(bot):
    await bot.add_cog(Skip(bot)) 