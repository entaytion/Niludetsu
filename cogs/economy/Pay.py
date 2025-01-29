import discord
from discord.ext import commands
from Niludetsu.utils.embed import create_embed
from Niludetsu.utils.database import get_user, save_user
from Niludetsu.core.base import EMOJIS

class Pay(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="pay", description="Перевести деньги другому пользователю")
    @discord.app_commands.describe(
        user="Пользователь, которому нужно перевести деньги",
        amount="Сумма для перевода"
    )
    async def pay(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        # Проверка на перевод самому себе
        if user.id == interaction.user.id:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Вы не можете перевести деньги самому себе.",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        # Проверка на бота
        if user.bot and user.id != 1264591814208262154:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Вы не можете перевести деньги боту.",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        # Проверка суммы
        if amount <= 0:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Сумма перевода должна быть больше 0.",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        # Получаем данные отправителя
        sender_id = str(interaction.user.id)
        sender_data = get_user(sender_id)

        if not sender_data:
            sender_data = {
                'balance': 0,
                'deposit': 0,
                'xp': 0,
                'level': 1,
                'roles': '[]'
            }
            save_user(sender_id, sender_data)

        # Проверка баланса отправителя
        if sender_data.get('balance', 0) < amount:
            await interaction.response.send_message(
                embed=create_embed(
                    description=f"У вас недостаточно средств.\n"
                              f"Ваш баланс: {sender_data.get('balance', 0):,} {EMOJIS['MONEY']}",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        # Получаем данные получателя
        receiver_id = str(user.id)
        receiver_data = get_user(receiver_id)

        if not receiver_data:
            receiver_data = {
                'balance': 0,
                'deposit': 0,
                'xp': 0,
                'level': 1,
                'roles': '[]'
            }

        # Выполняем перевод
        sender_data['balance'] = sender_data.get('balance', 0) - amount
        receiver_data['balance'] = receiver_data.get('balance', 0) + amount

        # Сохраняем изменения
        save_user(sender_id, sender_data)
        save_user(receiver_id, receiver_data)

        # Отправляем сообщение об успешном переводе
        await interaction.response.send_message(
            embed=create_embed(
                title="Перевод выполнен",
                description=f"Вы перевели {amount:,} {EMOJIS['MONEY']} пользователю {user.mention}\n"
                          f"Ваш текущий баланс: {sender_data['balance']:,} {EMOJIS['MONEY']}",
                color="GREEN"
            )
        )

async def setup(bot):
    await bot.add_cog(Pay(bot))
