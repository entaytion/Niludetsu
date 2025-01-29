import discord
from discord.ext import commands
import random
from Niludetsu.utils.embed import create_embed

class Pat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pat_gifs = [
            "https://i.imgur.com/2lacG7l.gif",
            "https://i.imgur.com/UWbKpx8.gif",
            "https://i.imgur.com/4ssddEQ.gif",
            "https://i.imgur.com/2k0MFIr.gif",
            "https://i.imgur.com/LUypjw3.gif",
            "https://i.imgur.com/F3cjr3n.gif",
            "https://i.imgur.com/NNOz81F.gif",
            "https://i.imgur.com/Wqn7XhV.gif",
            "https://i.imgur.com/TpbSx9F.gif",
            "https://i.imgur.com/YxZvwPI.gif"
        ]

    @discord.app_commands.command(name="pat", description="Погладить пользователя")
    @discord.app_commands.describe(member="Пользователь, которого вы хотите погладить")
    async def pat(self, interaction: discord.Interaction, member: discord.Member):
        if member.id == interaction.user.id:
            await interaction.response.send_message(
                embed=create_embed(
                    description="❌ Вы не можете погладить самого себя!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        if member.bot:
            await interaction.response.send_message(
                embed=create_embed(
                    description="❌ Вы не можете погладить бота!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        gif_url = random.choice(self.pat_gifs)
        embed = create_embed(
            description=f"✨ {interaction.user.mention} погладил(а) {member.mention}",
            color="BLUE"
        )
        embed.set_image(url=gif_url)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Pat(bot))