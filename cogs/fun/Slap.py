import discord
from discord.ext import commands
from Niludetsu import Embed, GifsAPI

class Slap(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.gifs_api = GifsAPI()

    @discord.app_commands.command(name="slap", description="Ударить пользователя")
    @discord.app_commands.describe(member="Пользователь, которого вы хотите ударить")
    async def slap(self, interaction: discord.Interaction, member: discord.Member):
        if member.id == interaction.user.id:
            await interaction.response.send_message(
                embed=Embed(
                    description="❌ Вы не можете ударить самого себя!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        if member.bot:
            await interaction.response.send_message(
                embed=Embed(
                    description="❌ Вы не можете ударить бота!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        gif_url = self.gifs_api.get_random_gif('slap')
        embed=Embed(
            description=f"👋 {interaction.user.mention} ударил(а) {member.mention}",
            color="BLUE"
        )
        embed.set_image(url=gif_url)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Slap(bot))