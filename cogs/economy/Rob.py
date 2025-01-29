import discord
from discord.ext import commands
from Niludetsu.utils.embed import create_embed
from Niludetsu.utils.database import get_user, save_user
from Niludetsu.utils.emojis import EMOJIS
from datetime import datetime, timedelta
import random

class Rob(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rob_cooldown = 7200  # 2 часа в секундах
        self.min_balance_to_rob = 1000  # Минимальный баланс для ограбления
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
                embed=create_embed(
                    description="Вы не можете ограбить самого себя.",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        # Проверка на бота
        if user.bot and user.id != 1264591814208262154:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Вы не можете ограбить бота.",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        # Получаем данные грабителя
        robber_id = str(interaction.user.id)
        robber_data = get_user(robber_id)

        if not robber_data:
            robber_data = {
                'balance': 0,
                'deposit': 0,
                'xp': 0,
                'level': 1,
                'roles': '[]',
                'last_rob': None
            }

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
                    embed=create_embed(
                        description=f"Вы слишком устали для ограбления.\n"
                                  f"Отдохните еще: **{hours}ч {minutes}м**",
                        color="RED"
                    ),
                    ephemeral=True
                )
                return

        # Получаем данные жертвы
        victim_id = str(user.id)
        victim_data = get_user(victim_id)

        if not victim_data or victim_data.get('balance', 0) < self.min_balance_to_rob:
            await interaction.response.send_message(
                embed=create_embed(
                    description=f"У этого пользователя слишком мало денег для ограбления.\n"
                              f"Минимальная сумма: {self.min_balance_to_rob:,} {EMOJIS['MONEY']}",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        # Проверяем успех ограбления
        if random.random() <= self.success_chance:
            # Успешное ограбление
            max_steal = int(victim_data['balance'] * self.max_rob_percent)
            stolen = random.randint(1, max_steal)

            # Обновляем балансы
            robber_data['balance'] = robber_data.get('balance', 0) + stolen
            victim_data['balance'] = victim_data.get('balance', 0) - stolen

            # Обновляем время последнего ограбления
            robber_data['last_rob'] = datetime.utcnow().isoformat()

            # Сохраняем изменения
            save_user(robber_id, robber_data)
            save_user(victim_id, victim_data)

            await interaction.response.send_message(
                embed=create_embed(
                    title="Успешное ограбление!",
                    description=f"Вы украли {stolen:,} {EMOJIS['MONEY']} у {user.mention}\n"
                              f"Ваш текущий баланс: {robber_data['balance']:,} {EMOJIS['MONEY']}",
                    color="GREEN"
                )
            )
        else:
            # Неудачное ограбление
            fine = random.randint(100, 1000)
            robber_data['balance'] = max(0, robber_data.get('balance', 0) - fine)
            robber_data['last_rob'] = datetime.utcnow().isoformat()
            save_user(robber_id, robber_data)

            await interaction.response.send_message(
                embed=create_embed(
                    title="Неудачное ограбление!",
                    description=f"Вас поймала полиция и оштрафовала на {fine:,} {EMOJIS['MONEY']}\n"
                              f"Ваш текущий баланс: {robber_data['balance']:,} {EMOJIS['MONEY']}",
                    color="RED"
                )
            )

async def setup(bot):
    await bot.add_cog(Rob(bot))
