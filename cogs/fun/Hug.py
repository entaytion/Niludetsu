import discord
from discord.ext import commands
from Niludetsu.utils.embed import Embed
from Niludetsu.api.Gifs import GifsAPI

class Hug(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.gifs_api = GifsAPI()

    @discord.app_commands.command(name="hug", description="Обнять пользователя")
    @discord.app_commands.describe(member="Пользователь, которого вы хотите обнять")
    async def hug(self, interaction: discord.Interaction, member: discord.Member):
        if member.id == interaction.user.id:
            await interaction.response.send_message(
                embed=Embed(
                    description="❌ Вы не можете обнять самого себя!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        if member.bot:
            await interaction.response.send_message(
                embed=Embed(
                    description="❌ Вы не можете обнять бота!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        gif_url = self.gifs_api.get_random_gif('hug')
        embed=Embed(
            description=f"🤗 {interaction.user.mention} обнял(а) {member.mention}",
            color="BLUE"
        )
        embed.set_image(url=gif_url)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Hug(bot))