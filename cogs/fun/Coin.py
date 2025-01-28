import discord
from discord.ext import commands
import random
from Niludetsu.utils.embed import create_embed

class Coin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="coin", description="Подбросить монетку")
    async def coin(self, interaction: discord.Interaction):
        result = random.choice(["Орёл", "Решка"])
        
        await interaction.response.send_message(
            embed=create_embed(
                title="🪙 Подбрасываю монетку...",
                description=f"**Выпало:** {result}",
                color="BLUE"
            )
        )

async def setup(bot):
    await bot.add_cog(Coin(bot))