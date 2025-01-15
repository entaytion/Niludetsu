import discord
import random
from discord.ext import commands
from utils import create_embed, get_user, save_user, FOOTER_ERROR, FOOTER_SUCCESS

class Casino(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="casino", description="Азартные игры")
    @discord.app_commands.describe(bet="Ставка на красное, черное, зелёное, чётное, нечётное",
                                   amount="Сумма для ставки")
    async def casino(self, interaction: discord.Interaction,
                     bet: str = None, 
                     amount: int = None):
        # Проверка ставки
        if bet not in ["красное", "черное", "зелёное", "чётное", "нечётное"]:
            embed = create_embed(
                description="Неверный выбор ставки. Доступные ставки: красное, черное, зелёное, чётное, нечётное.",
                footer=FOOTER_ERROR
            )
            await interaction.response.send_message(embed=embed)
            return

        if amount is None:
            embed = create_embed(
                description="Не указана сумма для ставки.",
                footer=FOOTER_ERROR
            )
            await interaction.response.send_message(embed=embed)
            return

        user_id = str(interaction.user.id)
        user_data = get_user(self.bot, user_id)

        if user_data['balance'] < amount: 
            embed = create_embed(
                description="Недостаточно средств для ставки.",
                footer=FOOTER_ERROR
            )
            await interaction.response.send_message(embed=embed)
            return

        # Возможные исходы
        outcomes = ['зелёное'] + list(range(1, 37))  
        result = random.choice(outcomes)  

        if result == 'зелёное':
            result_color = 'зелёное'  
            card_number = 0  
        else:
            result_color = "красное" if result % 2 == 0 else "чёрное"
            card_number = result

        # Определение выигрыша
        if bet == 'чётное':
            win = card_number != 0 and card_number % 2 == 0  
        elif bet == 'нечётное':
            win = card_number != 0 and card_number % 2 != 0  
        elif bet == 'зелёное':
            win = result == 'зелёное'  
        else:
            win = bet == result_color

        # Расчёт выигрыша
        multiplier = 2 if result_color in ["красное", "чёрное"] else 14 if result_color == "зелёное" else 2
        winnings = amount * multiplier if win else -amount

        # Обновление баланса
        user_data['balance'] += winnings
        save_user(user_id, user_data)

        embed = create_embed(
            title="Казино \"NaibalovaNet\"",
            description=f"<:aeOutlineDot:1266066158029770833> **Ваша ставка:** `{bet}`\n"
                        f"<:aeOutlineDot:1266066158029770833> **Выпавший результат:** `{result}`\n"
                        f"<:aeOutlineDot:1266066158029770833> **Выигрыш:** {winnings} <:aeMoney:1266066622561517781>\n"
                        f"<:aeOutlineDot:1266066158029770833> **Ваш баланс:** {user_data['balance']} <:aeMoney:1266066622561517781>",
            color=0xf20c3c
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Casino(bot))
