import discord
from discord.ext import commands
from discord import app_commands
from utils import create_embed, get_user, save_user, EMOJIS

class Pay(commands.Cog):
    def __init__(self, client):
        self.client = client

    @app_commands.command(name="pay", description="Перевести деньги другому пользователю")
    @app_commands.describe(user="Пользователь, которому переводятся деньги", amount="Сумма перевода")
    async def pay(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        sender_id = str(interaction.user.id)
        receiver_id = str(user.id)

        if user.bot:
            embed = create_embed(
                description="Нельзя переводить деньги ботам."
            )
            await interaction.response.send_message(embed=embed)
            return

        if interaction.user.id == user.id:
            embed = create_embed(
                description="Нельзя переводить деньги самому себе."
            )
            await interaction.response.send_message(embed=embed)
            return

        sender = get_user(self.client, sender_id)
        receiver = get_user(self.client, receiver_id)

        if amount <= 0:
            embed = create_embed(
                description="Сумма должна быть положительной."
            )
            await interaction.response.send_message(embed=embed)
            return

        if sender['balance'] < amount:
            embed = create_embed(
                description="У вас недостаточно средств."
            )
            await interaction.response.send_message(embed=embed)
            return

        sender['balance'] -= amount
        receiver['balance'] += amount

        save_user(sender_id, sender)
        save_user(receiver_id, receiver)

        embed = create_embed(
            title="Баланс обновлён.",
            description=f"{interaction.user.mention} перевёл {user.mention} {amount} {EMOJIS['MONEY']}"
        )
        await interaction.response.send_message(embed=embed)

async def setup(client):
    await client.add_cog(Pay(client))
