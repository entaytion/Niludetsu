import discord
from discord import app_commands
from discord.ext import commands
import wavelink
from utils import create_embed
from .Core import Core

class Volume(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.core = None
        
    async def cog_load(self):
        self.core = self.bot.get_cog('Core')

    @app_commands.command(name="volume", description="Изменить громкость музыки")
    @app_commands.describe(volume="Громкость от 0 до 100")
    async def volume(self, interaction: discord.Interaction, volume: int):
        await interaction.response.defer()
        
        try:
            if not 0 <= volume <= 100:
                await interaction.followup.send(
                    embed=create_embed(
                        description="Громкость должна быть от 0 до 100!"
                    )
                )
                return

            player = await self.core.get_player(interaction)
            if not player or not player.connected:
                await interaction.followup.send(
                    embed=create_embed(
                        description="Я не подключен к голосовому каналу!"
                    )
                )
                return

            current: wavelink.Track = player.current
            if not current:
                await interaction.followup.send(
                    embed=create_embed(
                        description="Сейчас ничего не играет!"
                    )
                )
                return

            await player.set_volume(volume)
            await interaction.followup.send(
                embed=create_embed(
                    description=f"Громкость установлена на {volume}%"
                )
            )
        except Exception as e:
            print(f"Error in volume command: {e}")
            await interaction.followup.send(
                embed=create_embed(
                    description="Произошла ошибка!"
                )
            )

async def setup(bot):
    await bot.add_cog(Volume(bot)) 