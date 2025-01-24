import discord
from discord.ext import commands
from utils import create_embed
import random

class Cry(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.cry_gifs = [
            "https://media.giphy.com/media/ROF8OQvDmxytW/giphy.gif",
            "https://media.giphy.com/media/L95W4wv8nnb9K/giphy.gif",
            "https://media.giphy.com/media/ShPv5tt0EM396/giphy.gif",
            "https://media.giphy.com/media/3fmRTfVIKMRiM/giphy.gif",
            "https://media.giphy.com/media/OPU6wzx8JrHna/giphy.gif"
        ]
        self.cry_messages = [
            "плачет от грусти... 😢",
            "рыдает в уголочке... 😭",
            "не может сдержать слёзы... 💔",
            "заливается слёзами... 😢",
            "схлипует... 😥"
        ]

    @discord.app_commands.command(name="cry", description="Поплакать")
    async def cry(self, interaction: discord.Interaction):
        try:
            embed = create_embed(
                description=f"{interaction.user.mention} {random.choice(self.cry_messages)}"
            )
            embed.set_image(url=random.choice(self.cry_gifs))
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Произошла ошибка при выполнении команды!"
                )
            )
            print(f"Ошибка у команды cry: {e}")

async def setup(client):
    await client.add_cog(Cry(client)) 