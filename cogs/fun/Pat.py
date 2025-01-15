import discord
from discord.ext import commands
from utils import create_embed, FOOTER_SUCCESS, FOOTER_ERROR
import random

class Pat(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.pat_gifs = [
            "https://media.giphy.com/media/5tmRHwTlHAA9WkVxTU/giphy.gif",
            "https://media.giphy.com/media/ARSp9T7wwxNcs/giphy.gif", 
            "https://media.giphy.com/media/109ltuoSQT212w/giphy.gif",
            "https://media.giphy.com/media/ye7OTQgwmVuVy/giphy.gif",
            "https://media.giphy.com/media/d7PyZJN7zqiR2/giphy.gif"
        ]
        self.pat_messages = [
            "нежно гладит",
            "ласково гладит",
            "гладит по голове",
            "заботливо гладит",
            "успокаивающе гладит"
        ]

    @discord.app_commands.command(name="pat", description="Погладить пользователя")
    @discord.app_commands.describe(user="Пользователь, которого вы хотите погладить")
    async def pat(self, interaction: discord.Interaction, user: discord.Member):
        if user.id == interaction.user.id:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Вы не можете погладить самого себя!",
                    footer=FOOTER_ERROR
                ),
                ephemeral=True
            )
            return
            
        embed = create_embed(
            description=f"🤚 {interaction.user.mention} {random.choice(self.pat_messages)} {user.mention}!",
            footer=FOOTER_SUCCESS
        )
        embed.set_image(url=random.choice(self.pat_gifs))
        
        await interaction.response.send_message(embed=embed)

async def setup(client):
    await client.add_cog(Pat(client))