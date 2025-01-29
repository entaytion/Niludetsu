import discord
from discord.ext import commands
from Niludetsu.utils.embed import create_embed
from Niludetsu.utils.database import get_user, save_user
from Niludetsu.core.base import EMOJIS
from datetime import datetime, timedelta
import random

class Work(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.jobs = [
            {"name": "Программист", "min_reward": 500, "max_reward": 1500},
            {"name": "Дизайнер", "min_reward": 400, "max_reward": 1200},
            {"name": "Писатель", "min_reward": 300, "max_reward": 1000},
            {"name": "Художник", "min_reward": 350, "max_reward": 1100},
            {"name": "Музыкант", "min_reward": 450, "max_reward": 1300},
            {"name": "Фотограф", "min_reward": 380, "max_reward": 1150},
            {"name": "Переводчик", "min_reward": 420, "max_reward": 1250},
            {"name": "Блогер", "min_reward": 460, "max_reward": 1400},
            {"name": "Юрист", "min_reward": 500, "max_reward": 1500},
            {"name": "Бухгалтер", "min_reward": 480, "max_reward": 1350},
            {"name": "Маркетолог", "min_reward": 440, "max_reward": 1200},
            {"name": "Директор", "min_reward": 550, "max_reward": 1600},
            {"name": "Продавец", "min_reward": 390, "max_reward": 1100},
            {"name": "Водитель", "min_reward": 410, "max_reward": 1150},
            {"name": "Уборщик", "min_reward": 370, "max_reward": 1050},
            {"name": "Повар", "min_reward": 430, "max_reward": 1200},
            {"name": "Учитель", "min_reward": 470, "max_reward": 1350},
            {"name": "Секретарь", "min_reward": 360, "max_reward": 1000}
        ]
        self.work_cooldown = 3600  # 1 час в секундах

    @discord.app_commands.command(name="work", description="Заработать деньги")
    async def work(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        user_data = get_user(user_id)

        if not user_data:
            user_data = {
                'balance': 0,
                'deposit': 0,
                'xp': 0,
                'level': 1,
                'roles': '[]',
                'last_work': None
            }

        # Проверяем, когда пользователь последний раз работал
        last_work = user_data.get('last_work')
        if last_work:
            last_work = datetime.fromisoformat(last_work)
            next_work = last_work + timedelta(seconds=self.work_cooldown)
            
            if datetime.utcnow() < next_work:
                time_left = next_work - datetime.utcnow()
                minutes = int(time_left.total_seconds() // 60)
                seconds = int(time_left.total_seconds() % 60)
                
                await interaction.response.send_message(
                    embed=create_embed(
                        description=f"Вы слишком устали для работы.\n"
                                  f"Отдохните еще: **{minutes}м {seconds}с**",
                        color="RED"
                    ),
                    ephemeral=True
                )
                return

        # Выбираем случайную работу
        job = random.choice(self.jobs)
        reward = random.randint(job['min_reward'], job['max_reward'])

        # Добавляем бонус за уровень (5% за каждый уровень)
        level_bonus = int(reward * (user_data.get('level', 1) - 1) * 0.05)
        total_reward = reward + level_bonus

        # Обновляем данные пользователя
        user_data['balance'] = user_data.get('balance', 0) + total_reward
        user_data['last_work'] = datetime.utcnow().isoformat()
        
        # Добавляем опыт за работу
        user_data['xp'] = user_data.get('xp', 0) + random.randint(10, 20)
        
        save_user(user_id, user_data)

        # Формируем сообщение
        description = [
            f"Вы поработали **{job['name']}** и заработали {reward:,} {EMOJIS['MONEY']}",
        ]
        
        if level_bonus > 0:
            description.append(f"Бонус за уровень: +{level_bonus:,} {EMOJIS['MONEY']}")
            
        description.append(f"\nВаш текущий баланс: {user_data['balance']:,} {EMOJIS['MONEY']}")

        await interaction.response.send_message(
            embed=create_embed(
                title="Работа выполнена!",
                description="\n".join(description),
                color="GREEN"
            )
        )

async def setup(bot):
    await bot.add_cog(Work(bot))
