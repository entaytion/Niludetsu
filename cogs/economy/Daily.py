import discord
from discord.ext import commands
from Niludetsu.utils.embed import create_embed
from Niludetsu.utils.database import get_user, save_user
from Niludetsu.utils.emojis import EMOJIS
from datetime import datetime, timedelta
import random

class Daily(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="daily", description="Получить ежедневную награду")
    async def daily(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        user_data = get_user(user_id)

        if not user_data:
            user_data = {
                'balance': 0,
                'deposit': 0,
                'xp': 0,
                'level': 1,
                'roles': '[]',
                'last_daily': None
            }

        # Проверяем, когда пользователь последний раз получал награду
        last_daily = user_data.get('last_daily')
        if last_daily:
            last_daily = datetime.fromisoformat(last_daily)
            next_daily = last_daily + timedelta(days=1)
            
            if datetime.utcnow() < next_daily:
                time_left = next_daily - datetime.utcnow()
                hours = int(time_left.total_seconds() // 3600)
                minutes = int((time_left.total_seconds() % 3600) // 60)
                
                await interaction.response.send_message(
                    embed=create_embed(
                        description=f"❌ Вы уже получили ежедневную награду\n"
                                  f"⏰ Следующую награду можно получить через: "
                                  f"**{hours}ч {minutes}м**",
                        color="RED"
                    ),
                    ephemeral=True
                )
                return

        # Рандомная награда от 100 до 1000
        reward = random.randint(100, 1000)

        # Обновляем данные пользователя
        user_data['balance'] = user_data.get('balance', 0) + reward
        user_data['last_daily'] = datetime.utcnow().isoformat()
        save_user(user_id, user_data)

        # Отправляем сообщение об успешном получении награды
        await interaction.response.send_message(
            embed=create_embed(
                title="🎁 Ежедневная награда",
                description=f"💰 Вы получили: **{reward:,}** {EMOJIS['MONEY']}\n"
                          f"💳 Баланс: **{user_data['balance']:,}** {EMOJIS['MONEY']}",
                color="GREEN"
            )
        )

async def setup(bot):
    await bot.add_cog(Daily(bot))
