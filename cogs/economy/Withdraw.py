import discord
from discord.ext import commands
from Niludetsu.utils.embed import create_embed
from Niludetsu.utils.database import get_user, save_user
from Niludetsu.core.base import EMOJIS

class Withdraw(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="withdraw", description="Снять деньги с банка")
    @discord.app_commands.describe(
        amount="Сумма для снятия с банка"
    )
    async def withdraw(self, interaction: discord.Interaction, amount: int):
        """
        Команда для снятия денег с банка
        
        Parameters
        ----------
        interaction : discord.Interaction
            Объект взаимодействия
        amount : int
            Сумма для снятия с банка
        """
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

        # Проверка баланса в банке
        if user_data.get('deposit', 0) < amount:
            await interaction.response.send_message(
                embed=create_embed(
                    description=f"У вас недостаточно средств в банке.\n"
                              f"Баланс в банке: {user_data.get('deposit', 0):,} {EMOJIS['MONEY']}",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        # Выполняем снятие из банка
        user_data['deposit'] = user_data.get('deposit', 0) - amount
        user_data['balance'] = user_data.get('balance', 0) + amount
        save_user(user_id, user_data)

        # Отправляем сообщение об успешном снятии
        await interaction.response.send_message(
            embed=create_embed(
                title="Деньги сняты с банка",
                description=f"Вы сняли {amount:,} {EMOJIS['MONEY']} с банка\n"
                          f"Баланс в банке: {user_data['deposit']:,} {EMOJIS['MONEY']}\n"
                          f"Наличные: {user_data['balance']:,} {EMOJIS['MONEY']}",
                color="GREEN"
            )
        )

async def setup(bot):
    await bot.add_cog(Withdraw(bot))
