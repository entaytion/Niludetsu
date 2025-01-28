import discord
from discord.ext import commands
import random
from Niludetsu.utils.embed import create_embed

class Kiss(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.kiss_gifs = [
            "https://i.imgur.com/WVSwvm6.gif",
            "https://i.imgur.com/eisk88U.gif",
            "https://i.imgur.com/0WWWvat.gif",
            "https://i.imgur.com/MGdlYsj.gif",
            "https://i.imgur.com/f86DzYb.gif",
            "https://i.imgur.com/4Ad9G7g.gif",
            "https://i.imgur.com/YbNv10F.gif",
            "https://i.imgur.com/pezK9rn.gif",
            "https://i.imgur.com/TNhm1V6.gif",
            "https://i.imgur.com/0WWWvat.gif"
        ]

    @discord.app_commands.command(name="kiss", description="Поцеловать пользователя")
    @discord.app_commands.describe(member="Пользователь, которого вы хотите поцеловать")
    async def kiss(self, interaction: discord.Interaction, member: discord.Member):
        if member.id == interaction.user.id:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Вы не можете поцеловать самого себя!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        gif_url = random.choice(self.kiss_gifs)
        await interaction.response.send_message(
            embed=create_embed(
                description=f"{interaction.user.mention} поцеловал(а) {member.mention}",
                image=gif_url,
                color="GREEN"
            )
        )

async def setup(bot):
    await bot.add_cog(Kiss(bot))