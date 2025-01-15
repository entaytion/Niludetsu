import discord
from discord.ext import commands
from utils import create_embed, FOOTER_SUCCESS, FOOTER_ERROR
import random

class Hug(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.hug_gifs = [
            "https://media.giphy.com/media/od5H3PmEG5EVq/giphy.gif", 
            "https://media.giphy.com/media/EvYHHSntaIl5m/giphy.gif",
            "https://media.giphy.com/media/PHZ7v9tfQu0o0/giphy.gif",
            "https://media.giphy.com/media/3bqtLDeiDtwhq/giphy.gif",
            "https://media.giphy.com/media/u9BxQbM5bxvwY/giphy.gif"
        ]
        self.hug_messages = [
            "нежно обнимает",
            "крепко обнимает",
            "заключает в объятия",
            "дарит тёплые объятия",
            "обнимает с любовью"
        ]

    @discord.app_commands.command(name="hug", description="Обнять пользователя")
    @discord.app_commands.describe(user="Пользователь, которого вы хотите обнять")
    async def hug(self, interaction: discord.Interaction, user: discord.Member):
        if user.id == interaction.user.id:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Вы не можете обнять самого себя!",
                    footer=FOOTER_ERROR
                ),
                ephemeral=True
            )
            return
            
        embed = create_embed(
            description=f"🤗 {interaction.user.mention} {random.choice(self.hug_messages)} {user.mention}!",
            footer=FOOTER_SUCCESS
        )
        embed.set_image(url=random.choice(self.hug_gifs))
        
        await interaction.response.send_message(embed=embed)

async def setup(client):
    await client.add_cog(Hug(client))