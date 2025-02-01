import discord
from discord.ext import commands
from Niludetsu.utils.embed import Embed
from Niludetsu.database import Database
from Niludetsu.utils.emojis import EMOJIS

class Pay(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    @discord.app_commands.command(name="pay", description="Перевести деньги другому пользователю")
    @discord.app_commands.describe(
        user="Пользователь, которому нужно перевести деньги",
        amount="Сумма для перевода"
    )
    async def pay(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        # Проверка на перевод самому себе
        if user.id == interaction.user.id:
            await interaction.response.send_message(
                embed=Embed(
                    description="Вы не можете перевести деньги самому себе.",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        # Проверка на бота
        if user.bot and user.id != 1264591814208262154:
            await interaction.response.send_message(
                embed=Embed(
                    description="Вы не можете перевести деньги боту.",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        # Проверка суммы
        if amount <= 0:
            await interaction.response.send_message(
                embed=Embed(
                    description="Сумма перевода должна быть больше 0.",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        # Получаем данные отправителя
        sender_id = str(interaction.user.id)
        sender_data = await self.db.ensure_user(sender_id)

        # Проверка баланса отправителя
        if sender_data.get('balance', 0) < amount:
            await interaction.response.send_message(
                embed=Embed(
                    description=f"У вас недостаточно средств.\n"
                              f"Ваш баланс: {sender_data.get('balance', 0):,} {EMOJIS['MONEY']}",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        # Получаем данные получателя
        receiver_id = str(user.id)
        receiver_data = await self.db.ensure_user(receiver_id)

        # Выполняем перевод
        new_sender_balance = sender_data.get('balance', 0) - amount
        new_receiver_balance = receiver_data.get('balance', 0) + amount

        # Сохраняем изменения
        await self.db.update(
            "users",
            where={"user_id": sender_id},
            values={"balance": new_sender_balance}
        )
        await self.db.update(
            "users",
            where={"user_id": receiver_id},
            values={"balance": new_receiver_balance}
        )

        # Отправляем сообщение об успешном переводе
        await interaction.response.send_message(
            embed=Embed(
                title="Перевод выполнен",
                description=f"Вы перевели {amount:,} {EMOJIS['MONEY']} пользователю {user.mention}\n"
                          f"Ваш текущий баланс: {new_sender_balance:,} {EMOJIS['MONEY']}",
                color="GREEN"
            )
        )

async def setup(bot):
    await bot.add_cog(Pay(bot))
