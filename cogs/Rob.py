import discord
import random
from datetime import datetime, timedelta
from discord import Interaction
from discord.ext import commands
from utils import create_embed, get_user, save_user, FOOTER_ERROR, FOOTER_SUCCESS

class Rob(commands.Cog):
    def __init__(self, client):
        self.client = client

    @discord.app_commands.command(name="rob", description="Попытка украсть деньги")
    @discord.app_commands.describe(user="Пользователь, у которого украдёте деньги")
    async def rob(self, interaction: Interaction, user: discord.Member):
        # Передаем self.client в get_user
        author_data = get_user(self.client, str(interaction.user.id))
        victim_data = get_user(self.client, str(user.id))

        if str(user.id) == '1264591814208262154':
            embed = create_embed(
                description="Вы не можете украсть деньги у казны сервера.",
                footer=FOOTER_ERROR
            )
            await interaction.response.send_message(embed=embed)
            return

        if interaction.user.id == user.id:
            embed = create_embed(
                description="Вы не можете украсть деньги у самого себя.",
                footer=FOOTER_ERROR
            )
            await interaction.response.send_message(embed=embed)
            return

        if victim_data.get('balance', 0) <= 0:
            embed = create_embed(
                description=f"У {user.mention} нету денег на балансе.",
                footer=FOOTER_ERROR
            )
            await interaction.response.send_message(embed=embed)
            return

        last_rob_time = author_data.get('last_rob')
        if last_rob_time and datetime.utcnow() < datetime.fromisoformat(last_rob_time) + timedelta(minutes=5):
            minutes_left = (datetime.fromisoformat(last_rob_time) + timedelta(minutes=5) - datetime.utcnow()).seconds // 60
            embed = create_embed(
                description=f"Вы не можете украсть деньги у {user.mention} еще {minutes_left} минут.",
                footer=FOOTER_ERROR
            )
            await interaction.response.send_message(embed=embed)
            return

        success_chance = random.randint(1, 10)
        if success_chance == 1:
            stolen_amount = random.uniform(0.01, victim_data['balance'])
            embed = create_embed(
                title="Успех!",
                description=f"Вы успешно украли у {user.mention} {stolen_amount:.2f} <:aeMoney:1266066622561517781>",
                footer=FOOTER_SUCCESS
            )
            author_data['balance'] += stolen_amount
            victim_data['balance'] -= stolen_amount
            save_user(self.client, str(interaction.user.id), author_data)
            save_user(self.client, str(user.id), victim_data)
        else:
            embed = create_embed(
                description=f"Не получилось украсть деньги у {user.mention}. Попробуйте еще раз.",
                footer=FOOTER_ERROR
            )

        author_data['last_rob'] = datetime.utcnow().isoformat()
        save_user(self.client, str(interaction.user.id), author_data)
        await interaction.response.send_message(embed=embed)

async def setup(client):
    await client.add_cog(Rob(client))
