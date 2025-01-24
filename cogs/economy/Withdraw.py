import discord
from discord import Interaction
from discord.ext import commands
from utils import create_embed, get_user, save_user, EMOJIS

class Withdraw(commands.Cog):
    def __init__(self, client):
        self.client = client

    @discord.app_commands.command(name="withdraw", description="Снятие баланса")
    @discord.app_commands.describe(amount="Сумма для снятия с банка")
    async def withdraw(self,
                      interaction: Interaction,
                      amount: int):
        user_id = str(interaction.user.id)

        user_data = get_user(self.client, user_id)

        if amount <= 0:
            embed = create_embed(
                title="Ошибка.",
                description="Сумма снятия не может быть 0 или отрицательной."
            )
            await interaction.response.send_message(embed=embed)
            return

        if user_data['deposit'] < amount:
            embed = create_embed(
                title="Ошибка.",
                description="У вас недостаточно средств для снятия."
            )
            await interaction.response.send_message(embed=embed)
            return

        user_data['deposit'] -= amount
        user_data['balance'] += amount

        save_user(user_id, user_data)

        deposit = user_data['deposit']
        balance = user_data['balance']
        embed = create_embed(
            title="Снятие с депозита.",
            description=f"Вы вывели {amount} {EMOJIS['MONEY']} с депозита.\nВаш баланс: {balance} {EMOJIS['MONEY']}.\nВаш депозит: {deposit} {EMOJIS['MONEY']}."
        )
        await interaction.response.send_message(embed=embed)

async def setup(client):
    await client.add_cog(Withdraw(client))
