import discord
from discord.ext import commands
from Niludetsu.utils.embed import Embed
from Niludetsu.api.Gifs import GifsAPI

class Pat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.gifs_api = GifsAPI()

    @discord.app_commands.command(name="pat", description="Погладить пользователя")
    @discord.app_commands.describe(member="Пользователь, которого вы хотите погладить")
    async def pat(self, interaction: discord.Interaction, member: discord.Member):
        if member.id == interaction.user.id:
            await interaction.response.send_message(
                embed=Embed(
                    description="❌ Вы не можете погладить самого себя!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        if member.bot:
            await interaction.response.send_message(
                embed=Embed(
                    description="❌ Вы не можете погладить бота!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        gif_url = self.gifs_api.get_random_gif('pat')
        embed=Embed(
            description=f"✋ {interaction.user.mention} погладил(а) {member.mention}",
            color="BLUE"
        )
        embed.set_image(url=gif_url)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Pat(bot))