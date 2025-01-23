import discord
from discord.ext import commands
import wavelink
from utils import create_embed, FOOTER_ERROR, FOOTER_SUCCESS
from .Core import Core

class Repeat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.core = None
        
    async def cog_load(self):
        self.core = self.bot.get_cog('Core')

    @discord.app_commands.command(name="repeat", description="Повторить текущий трек")
    async def repeat(self, interaction: discord.Interaction):
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

            if not player.current:
                await interaction.followup.send(
                    embed=create_embed(
                        description="Сейчас ничего не играет!",
                        footer=FOOTER_ERROR
                    ),
                    ephemeral=True
                )
                return

            guild_id = interaction.guild.id
            self.core.repeating[guild_id] = not self.core.repeating.get(guild_id, False)
            status = "включено" if self.core.repeating[guild_id] else "отключено"
            
            await interaction.followup.send(
                embed=create_embed(
                    description=f"Повторение трека {status}.",
                    footer=FOOTER_SUCCESS
                )
            )
        except Exception as e:
            print(f"Error in repeat command: {e}")
            await interaction.followup.send(
                embed=create_embed(
                    description="Произошла ошибка!",
                    footer=FOOTER_ERROR
                ),
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Repeat(bot)) 