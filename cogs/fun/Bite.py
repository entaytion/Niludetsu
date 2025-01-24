import discord
from discord.ext import commands
from utils import create_embed
import random

class Bite(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.bite_gifs = [
            "https://media.giphy.com/media/OqQOwXiCyJAmA/giphy.gif",
            "https://media.giphy.com/media/iGZJRDVEM6iOc/giphy.gif",
            "https://media.giphy.com/media/Q5FEkpS3pB1S8/giphy.gif",
            "https://media.giphy.com/media/LUIvcbR6yytz2/giphy.gif",
            "https://media.giphy.com/media/YT8woTY5Zqs7iUo5BS/giphy.gif"
        ]
        self.bite_messages = [
            "кусает",
            "делает ням-ням",
            "смакует",
            "оставляет след в зубах",
            "пробует на вкус"
        ]

    @discord.app_commands.command(name="bite", description="Укусить пользователя")
    @discord.app_commands.describe(user="Пользователь, которого вы хотите укусить")
    async def bite(self, interaction: discord.Interaction, user: discord.Member):
        if user.id == interaction.user.id:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Вы не можете укусить самого себя!"
                )
            )
            return
            
        embed = create_embed(
            description=f"😈 {interaction.user.mention} {random.choice(self.bite_messages)} {user.mention}!"
        )
        embed.set_image(url=random.choice(self.bite_gifs))
        
        await interaction.response.send_message(embed=embed)

async def setup(client):
    await client.add_cog(Bite(client)) 