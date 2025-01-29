import discord
from discord.ext import commands
import random
from Niludetsu.utils.embed import create_embed

class Cry(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cry_gifs = [
            "https://i.imgur.com/Ak5NQgp.gif",
            "https://i.imgur.com/zd4sYGO.gif",
            "https://i.imgur.com/e4LGfeZ.gif",
            "https://i.imgur.com/g8cZnZ4.gif",
            "https://i.imgur.com/HWL1UQ5.gif",
            "https://i.imgur.com/JYXTCy4.gif",
            "https://i.imgur.com/o8y8kbN.gif",
            "https://i.imgur.com/YgqSR9i.gif",
            "https://i.imgur.com/TpbSx9F.gif",
            "https://i.imgur.com/NuEQxbm.gif"
        ]

    @discord.app_commands.command(name="cry", description="Заплакать")
    async def cry(self, interaction: discord.Interaction):
        gif_url = random.choice(self.cry_gifs)
        embed = create_embed(
            description=f"😢 {interaction.user.mention} плачет",
            color="BLUE"
        )
        embed.set_image(url=gif_url)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Cry(bot)) 