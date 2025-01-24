import discord
from discord.ext import commands
import wavelink
from utils import create_embed
from .Core import Core

class Nightcore(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.core = None
        
    async def cog_load(self):
        self.core = self.bot.get_cog('Core')

    @discord.app_commands.command(name="nightcore", description="Включить/выключить эффект Nightcore")
    async def nightcore(self, interaction: discord.Interaction):
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

            guild_id = interaction.guild.id
            filters = wavelink.Filters()
            
            if not self.core.nightcore_enabled.get(guild_id, False):
                filters.timescale.set(speed=1.2, pitch=1.2, rate=1.0)
                self.core.nightcore_enabled[guild_id] = True
                status = "включен"
            else:
                filters = wavelink.Filters()  
                self.core.nightcore_enabled[guild_id] = False
                status = "выключен"

            await player.set_filters(filters)
            await interaction.followup.send(
                embed=create_embed(
                    description=f"Эффект Nightcore {status}!"
                )
            )
        except Exception as e:
            print(f"Error in nightcore command: {e}")
            await interaction.followup.send(
                embed=create_embed(
                    description="Произошла ошибка при установке эффекта!"
                )
            )

async def setup(bot):
    await bot.add_cog(Nightcore(bot)) 