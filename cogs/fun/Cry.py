import discord
from discord.ext import commands
from Niludetsu import Embed, GifsAPI

class Cry(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.gifs_api = GifsAPI()

    @discord.app_commands.command(name="cry", description="Заплакать")
    async def cry(self, interaction: discord.Interaction):
        gif_url = self.gifs_api.get_random_gif('cry')
        embed=Embed(
            description=f"😢 {interaction.user.mention} плачет",
            color="BLUE"
        )
        embed.set_image(url=gif_url)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Cry(bot)) 