import discord
from discord.ext import commands
from Niludetsu.utils.embed import Embed
from Niludetsu.api.Gifs import GifsAPI

class Bite(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.gifs_api = GifsAPI()

    @discord.app_commands.command(name="bite", description="Укусить пользователя")
    @discord.app_commands.describe(member="Пользователь, которого вы хотите укусить")
    async def bite(self, interaction: discord.Interaction, member: discord.Member):
        if member.id == interaction.user.id:
            await interaction.response.send_message(
                embed=Embed(
                    description="❌ Вы не можете укусить самого себя!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        if member.bot:
            await interaction.response.send_message(
                embed=Embed(
                    description="❌ Вы не можете укусить бота!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        gif_url = self.gifs_api.get_random_gif('bite')
        embed=Embed(
            description=f"🦷 {interaction.user.mention} укусил(а) {member.mention}",
            color="BLUE"
        )
        embed.set_image(url=gif_url)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Bite(bot)) 