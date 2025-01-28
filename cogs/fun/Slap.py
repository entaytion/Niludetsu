import discord
from discord.ext import commands
import random
from Niludetsu.utils.embed import create_embed

class Slap(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.slap_gifs = [
            "https://i.imgur.com/fm49srQ.gif",
            "https://i.imgur.com/4MQkDKm.gif",
            "https://i.imgur.com/o2SJYUS.gif",
            "https://i.imgur.com/oOCq3Bt.gif",
            "https://i.imgur.com/Agwwaj6.gif",
            "https://i.imgur.com/YA7g7h7.gif",
            "https://i.imgur.com/IGcyKPH.gif",
            "https://i.imgur.com/mIg8erJ.gif",
            "https://i.imgur.com/oRsaSyU.gif",
            "https://i.imgur.com/CwbYjBX.gif"
        ]

    @discord.app_commands.command(name="slap", description="Ударить пользователя")
    @discord.app_commands.describe(member="Пользователь, которого вы хотите ударить")
    async def slap(self, interaction: discord.Interaction, member: discord.Member):
        if member.id == interaction.user.id:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Вы не можете ударить самого себя!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        gif_url = random.choice(self.slap_gifs)
        await interaction.response.send_message(
            embed=create_embed(
                description=f"{interaction.user.mention} ударил(а) {member.mention}",
                image=gif_url,
                color="GREEN"
            )
        )

async def setup(bot):
    await bot.add_cog(Slap(bot))