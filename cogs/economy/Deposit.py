import discord
from discord.ext import commands
from Niludetsu.utils.embed import Embed
from Niludetsu.database import Database
from Niludetsu.utils.emojis import EMOJIS

class Deposit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    @discord.app_commands.command(name="deposit", description="Положить деньги в банк")
    @discord.app_commands.describe(
        amount="Сумма для внесения в банк"
    )
    async def deposit(self, interaction: discord.Interaction, amount: int):
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

        # Проверка баланса
        if user_data.get('balance', 0) < amount:
            await interaction.response.send_message(
                embed=Embed(
                    description=f"У вас недостаточно средств.\n"
                              f"Ваш баланс: {user_data.get('balance', 0):,} {EMOJIS['MONEY']}",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        # Выполняем перевод в банк
        new_balance = user_data.get('balance', 0) - amount
        new_deposit = user_data.get('deposit', 0) + amount
        
        await self.db.update(
            "users",
            where={"user_id": user_id},
            values={
                "balance": new_balance,
                "deposit": new_deposit
            }
        )

        # Отправляем сообщение об успешном внесении
        await interaction.response.send_message(
            embed=Embed(
                title="Деньги внесены в банк",
                description=f"Вы внесли {amount:,} {EMOJIS['MONEY']} в банк\n"
                          f"Баланс в банке: {new_deposit:,} {EMOJIS['MONEY']}\n"
                          f"Наличные: {new_balance:,} {EMOJIS['MONEY']}",
                color="GREEN"
            )
        )

async def setup(bot):
    await bot.add_cog(Deposit(bot))
