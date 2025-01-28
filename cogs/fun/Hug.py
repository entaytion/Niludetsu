import discord
from discord.ext import commands
import random
from Niludetsu.utils.embed import create_embed

class Hug(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.hug_gifs = [
            "https://i.imgur.com/r9aU2xv.gif",
            "https://i.imgur.com/wOmoeF8.gif",
            "https://i.imgur.com/nrdYNtL.gif",
            "https://i.imgur.com/BPLqSJC.gif",
            "https://i.imgur.com/ntqYLGl.gif",
            "https://i.imgur.com/v47M1S4.gif",
            "https://i.imgur.com/82xVqUg.gif",
            "https://i.imgur.com/4oLIrwj.gif",
            "https://i.imgur.com/6qYOUQF.gif",
            "https://i.imgur.com/UMm95sV.gif"
        ]

    @discord.app_commands.command(name="hug", description="Обнять пользователя")
    @discord.app_commands.describe(member="Пользователь, которого вы хотите обнять")
    async def hug(self, interaction: discord.Interaction, member: discord.Member):
        if member.id == interaction.user.id:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Вы не можете обнять самого себя!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        gif_url = random.choice(self.hug_gifs)
        await interaction.response.send_message(
            embed=create_embed(
                description=f"{interaction.user.mention} обнял(а) {member.mention}",
                image=gif_url,
                color="GREEN"
            )
        )

async def setup(bot):
    await bot.add_cog(Hug(bot))