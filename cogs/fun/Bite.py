import discord
from discord.ext import commands
import random
from Niludetsu.utils.embed import create_embed

class Bite(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bite_gifs = [
            "https://i.imgur.com/OE4aYl5.gif",
            "https://i.imgur.com/UbQWABX.gif",
            "https://i.imgur.com/P9L7FiW.gif",
            "https://i.imgur.com/HD5tMBh.gif",
            "https://i.imgur.com/qYUn6PI.gif",
            "https://i.imgur.com/K0e9bj5.gif",
            "https://i.imgur.com/YvTQtV0.gif",
            "https://i.imgur.com/FP0eXXD.gif",
            "https://i.imgur.com/8kdYbXz.gif",
            "https://i.imgur.com/YA7g7h7.gif"
        ]

    @discord.app_commands.command(name="bite", description="Укусить пользователя")
    @discord.app_commands.describe(member="Пользователь, которого вы хотите укусить")
    async def bite(self, interaction: discord.Interaction, member: discord.Member):
        if member.id == interaction.user.id:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Вы не можете укусить самого себя!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        gif_url = random.choice(self.bite_gifs)
        await interaction.response.send_message(
            embed=create_embed(
                description=f"{interaction.user.mention} укусил(а) {member.mention}",
                image=gif_url,
                color="GREEN"
            )
        )

async def setup(bot):
    await bot.add_cog(Bite(bot)) 