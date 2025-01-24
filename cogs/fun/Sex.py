import discord
from discord.ext import commands
from utils import create_embed, get_user
import random

class Sex(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.sex_gifs = [
            "https://media.giphy.com/media/11V54nIH3eDQK4/giphy.gif",
            "https://media.giphy.com/media/11V54nIH3eDQK4/giphy.gif",
            "https://media.giphy.com/media/11V54nIH3eDQK4/giphy.gif",
            "https://media.giphy.com/media/11V54nIH3eDQK4/giphy.gif",
            "https://media.giphy.com/media/11V54nIH3eDQK4/giphy.gif"
        ]
        self.sex_messages = [
            "занимается любовью с",
            "проводит страстную ночь с",
            "наслаждается моментом с",
            "разделяет интимный момент с",
            "предается страсти с"
        ]

    @discord.app_commands.command(name="sex", description="Заняться сексом с пользователем")
    @discord.app_commands.describe(user="Пользователь, с которым вы хотите заняться сексом")
    async def sex(self, interaction: discord.Interaction, user: discord.Member):
        if user.id == interaction.user.id:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Вы не можете заниматься этим сами с собой!"
                )
            )
            return

        # Проверяем, женат ли пользователь
        author_data = get_user(self.client, str(interaction.user.id))
        if not author_data:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Вы не зарегистрированы в системе!"
                )
            )
            return

        # Если пользователь женат и партнер не является целевым пользователем
        if author_data.get('spouse') and author_data.get('spouse') != str(user.id):
            spouse_member = interaction.guild.get_member(int(author_data['spouse']))
            spouse_mention = spouse_member.mention if spouse_member else "вашим партнером"
            
            await interaction.response.send_message(
                embed=create_embed(
                    description=f"Вы женаты с {spouse_mention}! Зрада это плохо!"
                )
            )
            return

        # Проверяем, женат ли целевой пользователь
        target_data = get_user(self.client, str(user.id))
        if target_data and target_data.get('spouse') and target_data['spouse'] != str(interaction.user.id):
            await interaction.response.send_message(
                embed=create_embed(
                    description="Этот пользователь уже в браке!"
                )
            )
            return
            
        embed = create_embed(
            description=f"💕 {interaction.user.mention} {random.choice(self.sex_messages)} {user.mention}!"
        )
        embed.set_image(url=random.choice(self.sex_gifs))
        
        await interaction.response.send_message(embed=embed)

async def setup(client):
    await client.add_cog(Sex(client)) 