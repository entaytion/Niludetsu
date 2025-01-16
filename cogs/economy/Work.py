import discord
import random
from datetime import datetime, timedelta
from discord import Interaction
from discord.ext import commands
from utils import get_user, save_user, create_embed, FOOTER_SUCCESS, FOOTER_ERROR, EMOJIS

class Work(commands.Cog):
    def __init__(self, client):
        self.client = client

    @discord.app_commands.command(name="work", description="Поработать и получить вознаграждение.")
    async def work(self, interaction: Interaction):
        user_id = str(interaction.user.id)

        # Передаем self.client в get_user
        user_data = get_user(self.client, user_id)
        if user_data is None:
            embed = create_embed(
                description="Пользователь не найден. Пожалуйста, зарегистрируйтесь сначала.",
                footer=FOOTER_ERROR
            )
            await interaction.response.send_message(embed=embed)
            return

        last_work = user_data.get('last_work')
        now = datetime.utcnow() + timedelta(hours=2)  # UTC + 2

        if last_work and now < datetime.fromisoformat(last_work) + timedelta(hours=1):
            time_remaining = (datetime.fromisoformat(last_work) + timedelta(hours=1) - now).total_seconds()
            hours, remainder = divmod(time_remaining, 3600)
            minutes, seconds = divmod(remainder, 60)
            embed = create_embed(
                description=f"Следующий раз поработать можно будет через **`{int(minutes)}` минут и `{int(seconds)}` секунд.**",
                footer=FOOTER_ERROR
            )
            await interaction.response.send_message(embed=embed)
            return

        jobs = [
            ("доставщиком пиццы", 500, 1000),
            ("офисным сотрудником", 500, 1000),
            ("продавцом-консультантом", 500, 1000),
            ("курьером", 500, 1000),
            ("баристой", 500, 1000),
            ("строителем", 500, 1000),
            ("библиотекарем", 500, 1000),
            ("аптекарем", 500, 1000),
            ("слесарем", 500, 1000),
            ("уборщиком", 500, 1000),
            ("учителем", 500, 1000),
            ("администратором", 500, 1000),
            ("официантом", 500, 1000),
            ("парикмахером", 500, 1000),
            ("фермером", 500, 1000),
            ("банкиром", 500, 1000),
            ("экскурсоводом", 500, 1000),
            ("архитектором", 500, 1000),
        ]

        job, min_amount, max_amount = random.choice(jobs)
        amount = random.randint(min_amount, max_amount)

        chance = random.randint(1, 1000)
        if chance == 1:  # редкая удача
            wallet_amount = random.randint(5000, 15000)
            embed = create_embed(
                title="Удача!",
                description=f"Вы нашли кошелек на улице и получили {wallet_amount} {EMOJIS['MONEY']}!",
            )
            user_data['balance'] += wallet_amount
        elif chance <= 50:  # штраф
            fine_amount = random.randint(100, 500)
            embed = create_embed(
                title="Штраф.",
                description=f"Вас оштрафовали на {fine_amount} {EMOJIS['MONEY']}!",
            )
            user_data['balance'] -= fine_amount
        else:  # обычная работа
            embed = create_embed(
                title="Работа",
                description=f"Вы поработали **{job}** и получили {amount} {EMOJIS['MONEY']}!",
            )
            user_data['balance'] += amount

        user_data['last_work'] = now.isoformat()
        save_user(user_id, user_data)

        await interaction.response.send_message(embed=embed)

async def setup(client):
    await client.add_cog(Work(client))
