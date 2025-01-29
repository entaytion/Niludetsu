import discord
from discord.ext import commands
from Niludetsu.utils.embed import create_embed
from Niludetsu.api.Gifs import GifsAPI

class Kiss(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.gifs_api = GifsAPI()

    @discord.app_commands.command(name="kiss", description="Поцеловать пользователя")
    @discord.app_commands.describe(member="Пользователь, которого вы хотите поцеловать")
    async def kiss(self, interaction: discord.Interaction, member: discord.Member):
        if member.id == interaction.user.id:
            await interaction.response.send_message(
                embed=create_embed(
                    description="❌ Вы не можете поцеловать самого себя!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        if member.bot:
            await interaction.response.send_message(
                embed=create_embed(
                    description="❌ Вы не можете поцеловать бота!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        gif_url = self.gifs_api.get_random_gif('kiss')
        embed = create_embed(
            description=f"💋 {interaction.user.mention} поцеловал(а) {member.mention}",
            color="BLUE"
        )
        embed.set_image(url=gif_url)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Kiss(bot))