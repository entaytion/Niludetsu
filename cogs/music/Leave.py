import discord
from discord.ext import commands
import wavelink
from utils import create_embed, FOOTER_ERROR, FOOTER_SUCCESS
from .Core import Core

class Leave(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.core = None
        
    async def cog_load(self):
        self.core = self.bot.get_cog('Core')

    @discord.app_commands.command(name="leave", description="Отключить бота от голосового канала")
    async def leave(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            player = await self.core.get_player(interaction)
            if not player or not player.connected:
                await interaction.followup.send(
                    embed=create_embed(
                        description="Я не подключен к голосовому каналу!",
                        footer=FOOTER_ERROR
                    ),
                    ephemeral=True
                )
                return
                
            await player.disconnect()
            await interaction.followup.send(
                embed=create_embed(
                    description="Отключился от голосового канала.",
                    footer=FOOTER_SUCCESS
                )
            )
        except Exception as e:
            print(f"Error in leave command: {e}")
            await interaction.followup.send(
                embed=create_embed(
                    description="Произошла ошибка!",
                    footer=FOOTER_ERROR
                ),
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Leave(bot)) 