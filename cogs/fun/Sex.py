import discord
from discord.ext import commands
import random
from Niludetsu.utils.embed import create_embed
from Niludetsu.utils.database import get_user

class Sex(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sex_gifs = [
            "https://i.imgur.com/YA7g7h7.gif",
            "https://i.imgur.com/4MQkDKm.gif",
            "https://i.imgur.com/o2SJYUS.gif",
            "https://i.imgur.com/oOCq3Bt.gif",
            "https://i.imgur.com/Agwwaj6.gif",
            "https://i.imgur.com/IGcyKPH.gif",
            "https://i.imgur.com/mIg8erJ.gif",
            "https://i.imgur.com/oRsaSyU.gif",
            "https://i.imgur.com/CwbYjBX.gif",
            "https://i.imgur.com/fm49srQ.gif"
        ]

    @discord.app_commands.command(name="sex", description="Заняться любовью с пользователем")
    @discord.app_commands.describe(member="Пользователь для любви")
    async def sex(self, interaction: discord.Interaction, member: discord.Member):
        if member.id == interaction.user.id:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Вы не можете заняться любовью с самим собой!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        if member.bot:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Вы не можете заняться любовью с ботом!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        # Проверяем брак
        user_data = get_user(str(interaction.user.id))
        target_data = get_user(str(member.id))

        if not user_data or not user_data.get('spouse'):
            await interaction.response.send_message(
                embed=create_embed(
                    description="Вы должны состоять в браке чтобы заниматься любовью!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        if str(member.id) != user_data['spouse']:
            spouse = interaction.guild.get_member(int(user_data['spouse']))
            await interaction.response.send_message(
                embed=create_embed(
                    description=f"Вы можете заниматься любовью только со своим супругом ({spouse.mention if spouse else 'партнером'})!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        gif_url = random.choice(self.sex_gifs)
        await interaction.response.send_message(
            embed=create_embed(
                description=f"{interaction.user.mention} занимается любовью с {member.mention}",
                image=gif_url,
                color="GREEN"
            )
        )

async def setup(bot):
    await bot.add_cog(Sex(bot)) 