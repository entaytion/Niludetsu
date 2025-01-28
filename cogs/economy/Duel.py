import discord
from discord.ext import commands
import random
import asyncio
from Niludetsu.utils.database import get_user, save_user
from Niludetsu.utils.embed import create_embed
from Niludetsu.core.base import EMOJIS

class Duel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_duels = {}

    @discord.app_commands.command(name="duel", description="Вызвать игрока на дуэль")
    @discord.app_commands.describe(
        opponent="Игрок, которого вы хотите вызвать на дуэль",
        bet="Сумма ставки"
    )
    async def duel(self, interaction: discord.Interaction, opponent: discord.Member, bet: int):
        if opponent.id == interaction.user.id:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Вы не можете вызвать на дуэль самого себя!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        if bet <= 0:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Ставка должна быть больше 0!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        challenger_id = str(interaction.user.id)
        opponent_id = str(opponent.id)

        # Проверяем, не находится ли кто-то из игроков уже в дуэли
        if challenger_id in self.active_duels or opponent_id in self.active_duels:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Один из игроков уже участвует в дуэли!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        challenger_data = get_user(challenger_id)
        opponent_data = get_user(opponent_id)

        # Создаем данные для новых пользователей
        if not challenger_data:
            challenger_data = {
                'balance': 0,
                'deposit': 0,
                'xp': 0,
                'level': 1,
                'roles': '[]'
            }
            save_user(challenger_id, challenger_data)

        if not opponent_data:
            opponent_data = {
                'balance': 0,
                'deposit': 0,
                'xp': 0,
                'level': 1,
                'roles': '[]'
            }
            save_user(opponent_id, opponent_data)

        # Проверяем балансы
        if challenger_data['balance'] < bet:
            await interaction.response.send_message(
                embed=create_embed(
                    description=f"У вас недостаточно средств для такой ставки!\n"
                              f"Ваш баланс: {challenger_data['balance']:,} {EMOJIS['MONEY']}",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        if opponent_data['balance'] < bet:
            await interaction.response.send_message(
                embed=create_embed(
                    description=f"У {opponent.mention} недостаточно средств для такой ставки!\n"
                              f"Баланс оппонента: {opponent_data['balance']:,} {EMOJIS['MONEY']}",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        # Создаем кнопки
        view = discord.ui.View(timeout=30)
        accept_button = discord.ui.Button(label="Принять", style=discord.ButtonStyle.green, custom_id="accept")
        decline_button = discord.ui.Button(label="Отклонить", style=discord.ButtonStyle.red, custom_id="decline")

        async def accept_callback(button_interaction: discord.Interaction):
            if button_interaction.user.id != opponent.id:
                await button_interaction.response.send_message(
                    embed=create_embed(
                        description="Это не ваша дуэль!",
                        color="RED"
                    ),
                    ephemeral=True
                )
                return

            # Снимаем ставки с обоих игроков
            challenger_data['balance'] -= bet
            opponent_data['balance'] -= bet
            save_user(challenger_id, challenger_data)
            save_user(opponent_id, opponent_data)

            # Начинаем дуэль
            self.active_duels[challenger_id] = True
            self.active_duels[opponent_id] = True

            await button_interaction.message.edit(view=None)
            await self.start_duel(button_interaction, interaction.user, opponent, bet)

        async def decline_callback(button_interaction: discord.Interaction):
            if button_interaction.user.id != opponent.id:
                await button_interaction.response.send_message(
                    embed=create_embed(
                        description="Это не ваша дуэль!",
                        color="RED"
                    ),
                    ephemeral=True
                )
                return

            await button_interaction.message.edit(
                embed=create_embed(
                    description=f"{opponent.mention} отклонил вызов на дуэль!",
                    color="RED"
                ),
                view=None
            )

        accept_button.callback = accept_callback
        decline_button.callback = decline_callback
        view.add_item(accept_button)
        view.add_item(decline_button)

        # Отправляем приглашение
        await interaction.response.send_message(
            embed=create_embed(
                title="Вызов на дуэль!",
                description=f"{interaction.user.mention} вызывает {opponent.mention} на дуэль!\n"
                          f"Ставка: {bet:,} {EMOJIS['MONEY']}",
                color="BLUE"
            ),
            view=view
        )

    async def start_duel(self, interaction: discord.Interaction, challenger: discord.Member, opponent: discord.Member, bet: int):
        # Анимация дуэли
        duel_message = await interaction.response.send_message(
            embed=create_embed(
                title="Дуэль началась!",
                description="Дуэлянты готовятся...",
                color="BLUE"
            )
        )

        await asyncio.sleep(2)
        await duel_message.edit(
            embed=create_embed(
                title="Дуэль началась!",
                description="3...",
                color="BLUE"
            )
        )

        await asyncio.sleep(1)
        await duel_message.edit(
            embed=create_embed(
                title="Дуэль началась!",
                description="2...",
                color="BLUE"
            )
        )

        await asyncio.sleep(1)
        await duel_message.edit(
            embed=create_embed(
                title="Дуэль началась!",
                description="1...",
                color="BLUE"
            )
        )

        await asyncio.sleep(1)
        await duel_message.edit(
            embed=create_embed(
                title="Дуэль началась!",
                description="ОГОНЬ!",
                color="BLUE"
            )
        )

        await asyncio.sleep(1)

        # Определяем победителя
        winner = random.choice([challenger, opponent])
        loser = opponent if winner == challenger else challenger

        # Обновляем балансы
        winner_data = get_user(str(winner.id))
        winner_data['balance'] += bet * 2
        save_user(str(winner.id), winner_data)

        # Удаляем дуэль из активных
        del self.active_duels[str(challenger.id)]
        del self.active_duels[str(opponent.id)]

        # Отправляем результат
        await duel_message.edit(
            embed=create_embed(
                title="Дуэль окончена!",
                description=f"**Победитель:** {winner.mention}\n"
                          f"**Проигравший:** {loser.mention}\n\n"
                          f"{EMOJIS['DOT']} **Выигрыш:** {bet * 2:,} {EMOJIS['MONEY']}",
                color="GREEN"
            )
        )

async def setup(bot):
    await bot.add_cog(Duel(bot))