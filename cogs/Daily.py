import discord
import random
from datetime import datetime, timedelta
from discord.ext import commands
from utils import create_embed, get_user, save_user, FOOTER_ERROR, FOOTER_SUCCESS

class Daily(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="daily", description="Получить ежедневный бонус")
    async def daily(self, interaction: discord.Interaction):
        user = interaction.user  
        user_id = str(user.id) 
        user_data = get_user(self.bot, user_id)  
        last_daily = user_data.get('last_daily')
        now = datetime.utcnow() + timedelta(hours=2) 

        # Проверяем, прошел ли 1 день с последнего получения бонуса
        if last_daily and now < datetime.fromisoformat(last_daily) + timedelta(days=1):
            time_remaining = (datetime.fromisoformat(last_daily) + timedelta(days=1) - now).total_seconds()
            hours, remainder = divmod(time_remaining, 3600)
            minutes, seconds = divmod(remainder, 60)
            embed = create_embed(
                title="Ошибка.",
                description=f"Бонус можно будет получить через **{int(hours)} часов, {int(minutes)} минут, {int(seconds)} секунд.**",
                footer=FOOTER_ERROR
            )
            await interaction.response.send_message(embed=embed)
            return

        # Если пользователь может получить бонус, начисляем случайную сумму
        reward_amount = random.randint(0, 100)
        user_data['balance'] += reward_amount 
        user_data['last_daily'] = now.isoformat() 

        # Сохраняем данные пользователя
        save_user(user_id, user_data)

        # Создаем и отправляем успешное сообщение
        embed = create_embed(
            title="Ежедневный бонус!",
            description=f"Вы получили {reward_amount} <:aeMoney:1266066622561517781>! Ваш баланс: {user_data['balance']} <:aeMoney:1266066622561517781>.",
            footer=FOOTER_SUCCESS
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Daily(bot))
