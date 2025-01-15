import discord
from discord.ext import commands
from utils import create_embed, get_user, save_user, FOOTER_ERROR, FOOTER_SUCCESS

class Deposit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="deposit", description="Пополнение баланса")
    @discord.app_commands.describe(amount="Сумма для пополнения")
    async def deposit(self, interaction: discord.Interaction, amount: int):
        user_id = str(interaction.user.id)
        user_data = get_user(self.bot, user_id)

        if user_data['balance'] < amount:
            embed = create_embed(
                title="Ошибка.",
                description="У вас недостаточно средств для пополнения.",
                footer=FOOTER_ERROR
            )
            await interaction.response.send_message(embed=embed)
            return

        if amount <= 0:
            embed = create_embed(
                title="Ошибка.",
                description="Сумма пополнения не может быть 0 или отрицательной.",
                footer=FOOTER_ERROR
            )
            await interaction.response.send_message(embed=embed)
            return

        user_data['balance'] -= amount
        user_data['deposit'] += amount
        save_user(user_id, user_data)
        balance = user_data['balance']
        deposit = user_data['deposit']
        embed = create_embed(
            title="Пополнение депозита.",
            description=f"Вы положили в депозит {amount} <:aeMoney:1266066622561517781>.\nВаш баланс: {balance} <:aeMoney:1266066622561517781>.\nВаш депозит: {deposit} <:aeMoney:1266066622561517781>.",
            footer=FOOTER_SUCCESS
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Deposit(bot))
