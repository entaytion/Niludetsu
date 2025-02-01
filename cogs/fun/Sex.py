import discord
from discord.ext import commands
from Niludetsu.utils.embed import Embed
from Niludetsu.database import Database
from Niludetsu.api.Gifs import GifsAPI

class Sex(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.gifs_api = GifsAPI()

    @discord.app_commands.command(name="sex", description="Заняться любовью с супругом")
    @discord.app_commands.describe(member="Ваш супруг")
    async def sex(self, interaction: discord.Interaction, member: discord.Member):
        if member.id == interaction.user.id:
            await interaction.response.send_message(
                embed=Embed(
                    description="❌ Вы не можете заняться любовью с самим собой!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        if member.bot:
            await interaction.response.send_message(
                embed=Embed(
                    description="❌ Вы не можете заняться любовью с ботом!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        # Проверяем брак
        user_data = await self.db.get_row("users", user_id=str(interaction.user.id))
        target_data = await self.db.get_row("users", user_id=str(member.id))

        if not user_data or not user_data.get('spouse'):
            await interaction.response.send_message(
                embed=Embed(
                    description="❌ Вы должны состоять в браке чтобы заниматься любовью!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        if str(member.id) != user_data['spouse']:
            spouse = interaction.guild.get_member(int(user_data['spouse']))
            await interaction.response.send_message(
                embed=Embed(
                    description=f"❌ Вы можете заниматься любовью только со своим супругом ({spouse.mention if spouse else 'партнером'})!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        gif_url = self.gifs_api.get_random_gif('sex')
        embed=Embed(
            description=f"💕 {interaction.user.mention} занимается любовью с {member.mention}",
            color="BLUE"
        )
        embed.set_image(url=gif_url)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Sex(bot)) 