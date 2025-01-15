import discord
from discord.ext import commands
from utils import create_embed, FOOTER_SUCCESS, FOOTER_ERROR
import random

class Kiss(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.kiss_gifs = [
            "https://media.giphy.com/media/bGm9FuBCGg4SY/giphy.gif",
            "https://media.giphy.com/media/FqBTvSNjNzeZG/giphy.gif", 
            "https://media.giphy.com/media/zkppEMFvRX5FC/giphy.gif",
            "https://media.giphy.com/media/12VXIxKaIEarL2/giphy.gif",
            "https://media.giphy.com/media/G3va31oEEnIkM/giphy.gif"
        ]
        self.kiss_messages = [
            "нежно целует",
            "страстно целует",
            "дарит поцелуй",
            "целует с любовью",
            "осыпает поцелуями"
        ]

    @discord.app_commands.command(name="kiss", description="Поцеловать пользователя")
    @discord.app_commands.describe(user="Пользователь, которого вы хотите поцеловать")
    async def kiss(self, interaction: discord.Interaction, user: discord.Member):
        if user.id == interaction.user.id:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Вы не можете поцеловать самого себя!",
                    footer=FOOTER_ERROR
                ),
                ephemeral=True
            )
            return
            
        embed = create_embed(
            description=f"💋 {interaction.user.mention} {random.choice(self.kiss_messages)} {user.mention}!",
            footer=FOOTER_SUCCESS
        )
        embed.set_image(url=random.choice(self.kiss_gifs))
        
        await interaction.response.send_message(embed=embed)

async def setup(client):
    await client.add_cog(Kiss(client))