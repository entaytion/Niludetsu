import discord
from discord.ext import commands
import random
from Niludetsu.utils.database import get_user, save_user
from Niludetsu.utils.embed import create_embed
from Niludetsu.core.base import EMOJIS

class Casino(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="casino", description="Сыграть в казино")
    @discord.app_commands.describe(bet="Сумма ставки")
    async def casino(self, interaction: discord.Interaction, bet: int):
        if bet <= 0:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Ставка должна быть больше 0!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

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

        if user_data['balance'] < bet:
            await interaction.response.send_message(
                embed=create_embed(
                    description=f"У вас недостаточно средств для такой ставки!\n"
                              f"Ваш баланс: {user_data['balance']:,} {EMOJIS['MONEY']}",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        user_data['balance'] -= bet
        save_user(user_id, user_data)

        number = random.randint(1, 100)
        winnings = 0
        color = "RED"

        if number <= 45:  # 45% шанс проигрыша
            result = "Вы проиграли!"
        elif number <= 80:  # 35% шанс выиграть x2
            winnings = bet * 2
            result = "Вы выиграли x2!"
            color = "GREEN"
        elif number <= 95:  # 15% шанс выиграть x3
            winnings = bet * 3
            result = "Вы выиграли x3!"
            color = "GREEN"
        else:  # 5% шанс выиграть x5
            winnings = bet * 5
            result = "Вы выиграли x5!"
            color = "GREEN"

        if winnings > 0:
            user_data = get_user(user_id)
            user_data['balance'] += winnings
            save_user(user_id, user_data)

        description = f"**{result}**\n"
        if winnings > 0:
            description += f"{EMOJIS['DOT']} **Выигрыш:** {winnings:,} {EMOJIS['MONEY']}"

        await interaction.response.send_message(
            embed=create_embed(
                title="Казино",
                description=description,
                color=color
            )
        )

async def setup(bot):
    await bot.add_cog(Casino(bot))
