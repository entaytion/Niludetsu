import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
from datetime import datetime
from Niludetsu.utils.embed import create_embed
from Niludetsu.core.base import EMOJIS
from Niludetsu.utils.decorators import has_mod_role

class Warns(commands.GroupCog, group_name="warns"):
    def __init__(self, bot):
        self.bot = bot
        self.db = sqlite3.connect('config/database.db')

    @app_commands.command(name="list", description="Показать список предупреждений пользователя")
    @app_commands.describe(user="Пользователь для просмотра предупреждений")
    @has_mod_role()
    async def warns_list(
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
            embed = create_embed(
                title=f"{EMOJIS['INFO']} Информация о предупреждениях",
                description=f"{EMOJIS['SUCCESS']} У {'вас' if user == interaction.user else user.mention} нет активных предупреждений!",
                color="GREEN"
            )
            embed.set_thumbnail(url=user.display_avatar.url)
            return await interaction.response.send_message(embed=embed)

        warnings_list = []
        for idx, (warning_id, mod_id, reason, timestamp) in enumerate(warnings, 1):
            mod = interaction.guild.get_member(mod_id)
            mod_name = mod.name if mod else "Неизвестный модератор"
            
            try:
                warn_time = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                time_str = warn_time.strftime('%d.%m.%Y %H:%M')
            except:
                time_str = "Неизвестное время"
            
            warnings_list.append(
                f"**Предупреждение #{idx}** (ID: {warning_id})\n"
                f"{EMOJIS['SHIELD']} **Модератор:** {mod_name}\n"
                f"{EMOJIS['REASON']} **Причина:** `{reason}`\n"
                f"{EMOJIS['TIME']} **Дата:** `{time_str}`\n"
            )

        embed = create_embed(
            title=f"{EMOJIS['WARN']} Предупреждения пользователя {user.name}",
            description="\n".join(warnings_list),
            color="YELLOW"
        )
        
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(
            name=f"{EMOJIS['STATS']} Статистика",
            value=f"**Всего предупреждений:** {len(warnings)}",
            inline=False
        )
        embed.set_footer(text=f"ID пользователя: {user.id}")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="info", description="Посмотреть информацию о конкретном предупреждении")
    @app_commands.describe(
        warning_id="ID предупреждения",
        user="Пользователь (необязательно)"
    )
    async def warn_info(
        self,
        interaction: discord.Interaction,
        warning_id: int,
        user: discord.Member = None
    ):
        cursor = self.db.cursor()
        
        if user:
            cursor.execute(
                """
                SELECT user_id, moderator_id, reason, timestamp
                FROM warnings
                WHERE id = ? AND user_id = ? AND guild_id = ? AND active = TRUE
                """,
                (warning_id, user.id, interaction.guild.id)
            )
        else:
            cursor.execute(
                """
                SELECT user_id, moderator_id, reason, timestamp
                FROM warnings
                WHERE id = ? AND guild_id = ? AND active = TRUE
                """,
                (warning_id, interaction.guild.id)
            )
            
        warning = cursor.fetchone()
        
        if not warning:
            return await interaction.response.send_message(
                embed=create_embed(
                    title=f"{EMOJIS['ERROR']} Ошибка",
                    description="Предупреждение с указанным ID не найдено!",
                    color="RED"
                )
            )
            
        user_id, mod_id, reason, timestamp = warning
        warned_user = interaction.guild.get_member(user_id)
        mod = interaction.guild.get_member(mod_id)
        
        try:
            warn_time = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            time_str = warn_time.strftime('%d.%m.%Y %H:%M')
        except:
            time_str = "Неизвестное время"
            
        embed = create_embed(
            title=f"{EMOJIS['INFO']} Информация о предупреждении #{warning_id}",
            color="BLUE"
        )
        
        if warned_user:
            embed.set_thumbnail(url=warned_user.display_avatar.url)
        
        embed.add_field(
            name=f"{EMOJIS['USER']} Пользователь",
            value=warned_user.mention if warned_user else "Пользователь покинул сервер",
            inline=False
        )
        embed.add_field(
            name=f"{EMOJIS['SHIELD']} Модератор",
            value=mod.mention if mod else "Неизвестный модератор",
            inline=False
        )
        embed.add_field(
            name=f"{EMOJIS['REASON']} Причина",
            value=f"```{reason}```",
            inline=False
        )
        embed.add_field(
            name=f"{EMOJIS['TIME']} Дата выдачи",
            value=f"`{time_str}`",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Warns(bot))