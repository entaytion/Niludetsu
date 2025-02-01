import discord
from discord.ext import commands
from Niludetsu.utils.embed import Embed
from Niludetsu.database import Database
from Niludetsu.utils.emojis import EMOJIS
from datetime import datetime, timedelta
import random

class Daily(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    @discord.app_commands.command(name="daily", description="Получить ежедневную награду")
    async def daily(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        user_data = await self.db.ensure_user(user_id)

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
                    embed=Embed(
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
        await self.db.update(
            "users",
            where={"user_id": user_id},
            values={
                "balance": user_data.get('balance', 0) + reward,
                "last_daily": datetime.utcnow().isoformat()
            }
        )

        # Отправляем сообщение об успешном получении награды
        await interaction.response.send_message(
            embed=Embed(
                title="🎁 Ежедневная награда",
                description=f"💰 Вы получили: **{reward:,}** {EMOJIS['MONEY']}\n"
                          f"💳 Баланс: **{user_data['balance'] + reward:,}** {EMOJIS['MONEY']}",
                color="GREEN"
            )
        )

async def setup(bot):
    await bot.add_cog(Daily(bot))
