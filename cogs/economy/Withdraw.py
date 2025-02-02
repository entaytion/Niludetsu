import discord
from discord.ext import commands
from Niludetsu.utils.embed import Embed
from Niludetsu.database import Database
from Niludetsu.utils.constants import Emojis

class Withdraw(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    @discord.app_commands.command(name="withdraw", description="Снять деньги с банка")
    @discord.app_commands.describe(
        amount="Сумма для снятия с банка"
    )
    async def withdraw(self, interaction: discord.Interaction, amount: int):
        # Проверка суммы
        if amount <= 0:
            await interaction.response.send_message(
                embed=Embed(
                    description="Сумма должна быть больше 0.",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        # Получаем данные пользователя
        user_id = str(interaction.user.id)
        user_data = await self.db.ensure_user(user_id)

        # Проверка баланса в банке
        if user_data.get('deposit', 0) < amount:
            await interaction.response.send_message(
                embed=Embed(
                    description=f"У вас недостаточно средств в банке.\n"
                              f"Баланс в банке: {user_data.get('deposit', 0):,} {Emojis.MONEY}",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        # Выполняем снятие из банка
        new_deposit = user_data.get('deposit', 0) - amount
        new_balance = user_data.get('balance', 0) + amount
        
        await self.db.update(
            "users",
            where={"user_id": user_id},
            values={
                "deposit": new_deposit,
                "balance": new_balance
            }
        )

        # Отправляем сообщение об успешном снятии
        await interaction.response.send_message(
            embed=Embed(
                title="Деньги сняты с банка",
                description=f"Вы сняли {amount:,} {Emojis.MONEY} с банка\n"
                          f"Баланс в банке: {new_deposit:,} {Emojis.MONEY}\n"
                          f"Наличные: {new_balance:,} {Emojis.MONEY}",
                color="GREEN"
            )
        )

async def setup(bot):
    await bot.add_cog(Withdraw(bot))
