import discord
from discord.ext import commands
from Niludetsu.utils.embed import create_embed
from Niludetsu.utils.database import get_user, save_user
from Niludetsu.utils.emojis import EMOJIS

class Deposit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="deposit", description="Положить деньги в банк")
    @discord.app_commands.describe(
        amount="Сумма для внесения в банк"
    )
    async def deposit(self, interaction: discord.Interaction, amount: int):
        # Проверка суммы
        if amount <= 0:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Сумма должна быть больше 0.",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        # Получаем данные пользователя
        user_id = str(interaction.user.id)
        user_data = get_user(user_id)

        if not user_data:
            user_data = {
                'balance': 0,
                'deposit': 0,
                'xp': 0,
                'level': 1,
                'roles': '[]'
            }
            save_user(user_id, user_data)

        # Проверка баланса
        if user_data.get('balance', 0) < amount:
            await interaction.response.send_message(
                embed=create_embed(
                    description=f"У вас недостаточно средств.\n"
                              f"Ваш баланс: {user_data.get('balance', 0):,} {EMOJIS['MONEY']}",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        # Выполняем перевод в банк
        user_data['balance'] = user_data.get('balance', 0) - amount
        user_data['deposit'] = user_data.get('deposit', 0) + amount
        save_user(user_id, user_data)

        # Отправляем сообщение об успешном внесении
        await interaction.response.send_message(
            embed=create_embed(
                title="Деньги внесены в банк",
                description=f"Вы внесли {amount:,} {EMOJIS['MONEY']} в банк\n"
                          f"Баланс в банке: {user_data['deposit']:,} {EMOJIS['MONEY']}\n"
                          f"Наличные: {user_data['balance']:,} {EMOJIS['MONEY']}",
                color="GREEN"
            )
        )

async def setup(bot):
    await bot.add_cog(Deposit(bot))
