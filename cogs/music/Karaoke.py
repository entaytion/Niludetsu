import discord
from discord.ext import commands
import wavelink
from utils import create_embed
from .Core import Core

class Karaoke(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.core = None
        
    async def cog_load(self):
        self.core = self.bot.get_cog('Core')

    @discord.app_commands.command(name="karaoke", description="Включить/выключить режим караоке")
    async def karaoke(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            if not await self.core.check_voice(interaction):
                return
                
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
            
            if not self.core.karaoke_enabled.get(guild_id, False):
                # Настройки фильтра караоке
                filters.karaoke.set(
                    level=1.0,
                    mono_level=1.0,
                    filter_band=220.0,
                    filter_width=100.0
                )
                self.core.karaoke_enabled[guild_id] = True
                status = "включен"
            else:
                filters = wavelink.Filters()  # Сброс всех фильтров
                self.core.karaoke_enabled[guild_id] = False
                status = "выключен"

            await player.set_filters(filters)
            await interaction.followup.send(
                embed=create_embed(
                    description=f"Режим караоке {status}!"
                )
            )
        except Exception as e:
            print(f"Error in karaoke command: {e}")
            await interaction.followup.send(
                embed=create_embed(
                    description="Произошла ошибка при установке режима караоке!"
                )
            )

async def setup(bot):
    await bot.add_cog(Karaoke(bot)) 