import discord
from discord.ext import commands
from utils import create_embed, FOOTER_SUCCESS, FOOTER_ERROR
import random

class Slap(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.slap_gifs = [
            "https://media.giphy.com/media/Zau0yrl17uzdK/giphy.gif", 
            "https://media.giphy.com/media/Gf3AUz3eBNbTW/giphy.gif",
            "https://media.giphy.com/media/k1uYB5LvlBZqU/giphy.gif",
            "https://media.giphy.com/media/tX29X2Dx3sAXS/giphy.gif",
            "https://media.giphy.com/media/xUNd9HZq1itMkiK652/giphy.gif"
        ]
        self.slap_messages = [
            "сильно бьёт",
            "даёт пощёчину",
            "шлёпает",
            "отвешивает подзатыльник",
            "наказывает"
        ]

    @discord.app_commands.command(name="slap", description="Ударить пользователя")
    @discord.app_commands.describe(user="Пользователь, которого вы хотите ударить")
    async def slap(self, interaction: discord.Interaction, user: discord.Member):
        if user.id == interaction.user.id:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Вы не можете ударить самого себя!",
                    footer=FOOTER_ERROR
                ),
                ephemeral=True
            )
            return
            
        embed = create_embed(
            description=f"👋 {interaction.user.mention} {random.choice(self.slap_messages)} {user.mention}!",
            footer=FOOTER_SUCCESS
        )
        embed.set_image(url=random.choice(self.slap_gifs))
        
        await interaction.response.send_message(embed=embed)

async def setup(client):
    await client.add_cog(Slap(client))