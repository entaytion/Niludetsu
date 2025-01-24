import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
from datetime import datetime
from utils import create_embed

class Warns(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = sqlite3.connect('config/database.db')

    @app_commands.command(name="warns", description="Посмотреть предупреждения пользователя")
    @app_commands.describe(user="Пользователь для просмотра предупреждений")
    async def warns(
        self,
        interaction: discord.Interaction,
        user: discord.Member = None
    ):
        if user is None:
            user = interaction.user

        cursor = self.db.cursor()
        cursor.execute(
            """
            SELECT id, moderator_id, reason, timestamp
            FROM warnings
            WHERE user_id = ? AND guild_id = ? AND active = TRUE
            ORDER BY timestamp DESC
            """,
            (user.id, interaction.guild.id)
        )
        warnings = cursor.fetchall()

        if not warnings:
            return await interaction.response.send_message(
                embed=create_embed(
                    description=f"У {'вас' if user == interaction.user else user.mention} нет активных предупреждений!"
                )
            )

        # Формуємо список попереджень
        warnings_list = []
        for warning_id, mod_id, reason, timestamp in warnings:
            mod = interaction.guild.get_member(mod_id)
            mod_name = mod.name if mod else "Неизвестный модератор"
            
            # Конвертуємо timestamp в datetime
            try:
                warn_time = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                time_str = warn_time.strftime('%d.%m.%Y %H:%M')
            except:
                time_str = "Неизвестное время"
            
            warnings_list.append(
                f"**ID:** {warning_id}\n"
                f"**Модератор:** {mod_name}\n"
                f"**Причина:** `{reason}`\n"
                f"**Дата:** `{time_str}`\n"
            )

        # Створюємо embed з попередженнями
        embed = create_embed(
            title=f"⚠️ Предупреждения {'(ваши)' if user == interaction.user else user.name}",
            description="\n".join(warnings_list)
        )
        
        # Додаємо кількість попереджень як поле
        embed.add_field(
            name="Всего предупреждений",
            value=str(len(warnings)),
            inline=False
        )
        
        await interaction.response.send_message(
            embed=embed
        )

async def setup(bot):
    await bot.add_cog(Warns(bot)) 