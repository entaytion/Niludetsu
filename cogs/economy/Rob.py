import discord
from discord.ext import commands
from Niludetsu.utils.embed import Embed
from Niludetsu.database import Database
from Niludetsu.utils.constants import Emojis
from datetime import datetime, timedelta
import random

class Rob(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.rob_cooldown = 7200  # 2 часа в секундах
        self.success_chance = 0.4  # 40% шанс успеха
        self.max_rob_percent = 0.3  # Максимальный процент кражи (30%)

    @discord.app_commands.command(name="rob", description="Попытаться ограбить пользователя")
    @discord.app_commands.describe(
        user="Пользователь, которого хотите ограбить"
    )
    async def rob(self, interaction: discord.Interaction, user: discord.Member):
        # Проверка на ограбление самого себя
        if user.id == interaction.user.id:
            await interaction.response.send_message(
                embed=Embed(
                    description="Вы не можете ограбить самого себя.",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        # Проверка на бота
        if user.bot and user.id != 1264591814208262154:
            await interaction.response.send_message(
                embed=Embed(
                    description="Вы не можете ограбить бота.",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        # Получаем данные грабителя
        robber_id = str(interaction.user.id)
        robber_data = await self.db.ensure_user(robber_id)

        # Проверяем кулдаун
        last_rob = robber_data.get('last_rob')
        if last_rob:
            last_rob = datetime.fromisoformat(last_rob)
            next_rob = last_rob + timedelta(seconds=self.rob_cooldown)
            
            if datetime.utcnow() < next_rob:
                time_left = next_rob - datetime.utcnow()
                hours = int(time_left.total_seconds() // 3600)
                minutes = int((time_left.total_seconds() % 3600) // 60)
                
                await interaction.response.send_message(
                    embed=Embed(
                        description=f"Вы слишком устали для ограбления.\n"
                                  f"Отдохните еще: **{hours}ч {minutes}м**",
                        color="RED"
                    ),
                    ephemeral=True
                )
                return

        # Получаем данные жертвы
        victim_id = str(user.id)
        victim_data = await self.db.ensure_user(victim_id)

        # Проверяем успех ограбления
        if random.random() <= self.success_chance:
            # Успешное ограбление
            max_steal = int(victim_data['balance'] * self.max_rob_percent)
            stolen = random.randint(1, max(1, max_steal))

            # Обновляем балансы
            new_robber_balance = robber_data.get('balance', 0) + stolen
            new_victim_balance = victim_data.get('balance', 0) - stolen

            # Обновляем время последнего ограбления и баланс грабителя
            await self.db.update(
                "users",
                where={"user_id": robber_id},
                values={
                    "balance": new_robber_balance,
                    "last_rob": datetime.utcnow().isoformat()
                }
            )

            # Обновляем баланс жертвы
            await self.db.update(
                "users",
                where={"user_id": victim_id},
                values={"balance": new_victim_balance}
            )

            await interaction.response.send_message(
                embed=Embed(
                    title="Успешное ограбление!",
                    description=f"Вы украли {stolen:,} {Emojis.MONEY} у {user.mention}\n"
                              f"Ваш текущий баланс: {new_robber_balance:,} {Emojis.MONEY}",
                    color="GREEN"
                )
            )
        else:
            # Неудачное ограбление
            fine = random.randint(100, 1000)
            new_robber_balance = max(0, robber_data.get('balance', 0) - fine)
            
            await self.db.update(
                "users",
                where={"user_id": robber_id},
                values={
                    "balance": new_robber_balance,
                    "last_rob": datetime.utcnow().isoformat()
                }
            )

            await interaction.response.send_message(
                embed=Embed(
                    title="Неудачное ограбление!",
                    description=f"Вас поймала полиция и оштрафовала на {fine:,} {Emojis.MONEY}\n"
                              f"Ваш текущий баланс: {new_robber_balance:,} {Emojis.MONEY}",
                    color="RED"
                )
            )

async def setup(bot):
    await bot.add_cog(Rob(bot))
