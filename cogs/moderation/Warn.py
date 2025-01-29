import discord
from discord.ext import commands
from discord import app_commands
import yaml
import sqlite3
from datetime import datetime, timedelta
from Niludetsu.utils.embed import create_embed
from Niludetsu.utils.database import initialize_table, TABLES_SCHEMAS
from Niludetsu.utils.decorators import has_helper_role, command_cooldown
from Niludetsu.utils.emojis import EMOJIS

# Загрузка конфигурации
with open('config/config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

MOD_ROLE_ID = int(config.get('moderation', {}).get('mod_role', 0))
MAX_WARNINGS = int(config.get('moderation', {}).get('max_warnings', 3))

def has_mod_role():
    async def predicate(interaction: discord.Interaction):
        if MOD_ROLE_ID == 0:
            return False
        return interaction.user.guild_permissions.administrator or any(
            role.id == MOD_ROLE_ID for role in interaction.user.roles
        )
    return app_commands.check(predicate)

def has_helper_role():
    async def predicate(interaction: discord.Interaction):
        if MOD_ROLE_ID == 0:
            return False
        return interaction.user.guild_permissions.administrator or any(
            role.id == MOD_ROLE_ID for role in interaction.user.roles
        )
    return app_commands.check(predicate)

class Warn(commands.GroupCog, group_name="warn"):
    def __init__(self, bot):
        self.bot = bot
        self.db = sqlite3.connect('config/database.db')
        self.setup_database()

    def setup_database(self):
        initialize_table('warnings', TABLES_SCHEMAS['warnings'])

    def get_user_active_warnings(self, user_id: int, guild_id: int) -> int:
        cursor = self.db.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM warnings WHERE user_id = ? AND guild_id = ? AND active = TRUE",
            (user_id, guild_id)
        )
        return cursor.fetchone()[0]

    @app_commands.command(name="add", description="Выдать предупреждение пользователю")
    @app_commands.describe(
        user="Пользователь для предупреждения",
        reason="Причина предупреждения"
    )
    @has_helper_role()
    @command_cooldown()
    async def warn_add(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        reason: str = "Причина не указана"
    ):
        # Проверки
        if user.id == interaction.user.id:
            return await interaction.response.send_message(
                embed=create_embed(
                    title=f"{EMOJIS['ERROR']} Ошибка",
                    description="Вы не можете выдать предупреждение самому себе!",
                    color="RED"
                ),
                ephemeral=True
            )

        if user.bot:
            return await interaction.response.send_message(
                embed=create_embed(
                    title=f"{EMOJIS['ERROR']} Ошибка",
                    description="Нельзя выдать предупреждение боту!",
                    color="RED"
                ),
                ephemeral=True
            )

        if user.guild_permissions.administrator:
            return await interaction.response.send_message(
                embed=create_embed(
                    title=f"{EMOJIS['ERROR']} Ошибка",
                    description="Нельзя выдать предупреждение администратору!",
                    color="RED"
                ),
                ephemeral=True
            )

        # Отправляем сообщение о начале процесса
        progress_embed = create_embed(
            title=f"{EMOJIS['LOADING']} Выдача предупреждения",
            description=f"Выдаю предупреждение для {user.mention}...",
            color="YELLOW"
        )
        await interaction.response.send_message(embed=progress_embed)

        # Добавляем предупреждение в базу данных
        cursor = self.db.cursor()
        cursor.execute(
            "INSERT INTO warnings (user_id, guild_id, moderator_id, reason) VALUES (?, ?, ?, ?)",
            (user.id, interaction.guild.id, interaction.user.id, reason)
        )
        self.db.commit()

        warning_count = self.get_user_active_warnings(user.id, interaction.guild.id)

        # Создаем эмбед для личного сообщения
        dm_embed = create_embed(
            title=f"{EMOJIS['WARNING']} Предупреждение получено",
            description=(
                f"**Сервер:** {interaction.guild.name}\n"
                f"**Модератор:** {interaction.user.mention}\n"
                f"**Причина:** {reason}\n"
                f"**Предупреждения:** `{warning_count}/{MAX_WARNINGS}`"
            ),
            color="RED"
        )

        # Пытаемся отправить личное сообщение
        dm_sent = False
        try:
            await user.send(embed=dm_embed)
            dm_sent = True
        except discord.Forbidden:
            pass

        # Создаем эмбед для канала
        warn_embed = create_embed(
            title=f"{EMOJIS['WARNING']} Выдано предупреждение",
            color="RED"
        )

        warn_embed.add_field(
            name=f"{EMOJIS['USER']} Пользователь",
            value=f"{user.mention} (`{user.id}`)",
            inline=True
        )
        warn_embed.add_field(
            name=f"{EMOJIS['SHIELD']} Модератор",
            value=interaction.user.mention,
            inline=True
        )
        warn_embed.add_field(
            name=f"{EMOJIS['WARNING']} Предупреждения",
            value=f"`{warning_count}/{MAX_WARNINGS}`",
            inline=True
        )
        warn_embed.add_field(
            name=f"{EMOJIS['REASON']} Причина",
            value=f"```{reason}```",
            inline=False
        )
        warn_embed.add_field(
            name=f"{EMOJIS['MESSAGE']} Личное сообщение",
            value=f"{'✅ Отправлено' if dm_sent else '❌ Не удалось отправить'}",
            inline=False
        )

        await interaction.edit_original_response(embed=warn_embed)

    @app_commands.command(name="remove", description="Удалить предупреждение у пользователя")
    @app_commands.describe(
        user="Пользователь",
        warning_id="ID предупреждения для удаления"
    )
    @has_helper_role()
    @command_cooldown()
    async def warn_remove(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        warning_id: int
    ):
        # Отправляем сообщение о начале процесса
        progress_embed = create_embed(
            title=f"{EMOJIS['LOADING']} Удаление предупреждения",
            description=f"Удаляю предупреждение у {user.mention}...",
            color="YELLOW"
        )
        await interaction.response.send_message(embed=progress_embed)

        cursor = self.db.cursor()
        
        # Проверяем, существует ли предупреждение
        cursor.execute(
            "SELECT * FROM warnings WHERE id = ? AND user_id = ? AND guild_id = ? AND active = TRUE",
            (warning_id, user.id, interaction.guild.id)
        )
        warning = cursor.fetchone()
        
        if not warning:
            return await interaction.edit_original_response(
                embed=create_embed(
                    title=f"{EMOJIS['ERROR']} Ошибка",
                    description="Предупреждение не найдено!",
                    color="RED"
                )
            )

        # Деактивируем предупреждение
        cursor.execute(
            "UPDATE warnings SET active = FALSE WHERE id = ?",
            (warning_id,)
        )
        self.db.commit()

        warning_count = self.get_user_active_warnings(user.id, interaction.guild.id)

        # Пытаемся отправить личное сообщение
        dm_sent = False
        try:
            await user.send(
                embed=create_embed(
                    title=f"{EMOJIS['SUCCESS']} Предупреждение снято",
                    description=(
                        f"**Сервер:** {interaction.guild.name}\n"
                        f"**Модератор:** {interaction.user.mention}\n"
                        f"**Предупреждения:** `{warning_count}/{MAX_WARNINGS}`"
                    ),
                    color="GREEN"
                )
            )
            dm_sent = True
        except:
            pass

        # Создаем эмбед для канала
        remove_embed = create_embed(
            title=f"{EMOJIS['SUCCESS']} Предупреждение удалено",
            color="GREEN"
        )

        remove_embed.add_field(
            name=f"{EMOJIS['USER']} Пользователь",
            value=f"{user.mention} (`{user.id}`)",
            inline=True
        )
        remove_embed.add_field(
            name=f"{EMOJIS['SHIELD']} Модератор",
            value=interaction.user.mention,
            inline=True
        )
        remove_embed.add_field(
            name=f"{EMOJIS['WARNING']} Предупреждения",
            value=f"`{warning_count}/{MAX_WARNINGS}`",
            inline=True
        )
        remove_embed.add_field(
            name=f"{EMOJIS['MESSAGE']} Личное сообщение",
            value=f"{'✅ Отправлено' if dm_sent else '❌ Не удалось отправить'}",
            inline=False
        )

        await interaction.edit_original_response(embed=remove_embed)

    @app_commands.command(name="clear", description="Удалить все предупреждения у пользователя")
    @app_commands.describe(user="Пользователь для очистки предупреждений")
    @has_helper_role()
    @command_cooldown()
    async def warn_clear(
        self,
        interaction: discord.Interaction,
        user: discord.Member
    ):
        # Отправляем сообщение о начале процесса
        progress_embed = create_embed(
            title=f"{EMOJIS['LOADING']} Очистка предупреждений",
            description=f"Удаляю все предупреждения у {user.mention}...",
            color="YELLOW"
        )
        await interaction.response.send_message(embed=progress_embed)

        cursor = self.db.cursor()
        
        # Получаем количество активных предупреждений до очистки
        warnings_before = self.get_user_active_warnings(user.id, interaction.guild.id)
        
        if warnings_before == 0:
            return await interaction.edit_original_response(
                embed=create_embed(
                    title=f"{EMOJIS['INFO']} Информация",
                    description=f"У пользователя {user.mention} нет активных предупреждений",
                    color="BLUE"
                )
            )

        # Деактивируем все предупреждения
        cursor.execute(
            "UPDATE warnings SET active = FALSE WHERE user_id = ? AND guild_id = ? AND active = TRUE",
            (user.id, interaction.guild.id)
        )
        self.db.commit()

        # Пытаемся отправить личное сообщение
        dm_sent = False
        try:
            await user.send(
                embed=create_embed(
                    title=f"{EMOJIS['SUCCESS']} Предупреждения сняты",
                    description=(
                        f"**Сервер:** {interaction.guild.name}\n"
                        f"**Модератор:** {interaction.user.mention}\n"
                        f"**Снято предупреждений:** `{warnings_before}`"
                    ),
                    color="GREEN"
                )
            )
            dm_sent = True
        except:
            pass

        # Создаем эмбед для канала
        clear_embed = create_embed(
            title=f"{EMOJIS['SUCCESS']} Предупреждения очищены",
            color="GREEN"
        )

        clear_embed.add_field(
            name=f"{EMOJIS['USER']} Пользователь",
            value=f"{user.mention} (`{user.id}`)",
            inline=True
        )
        clear_embed.add_field(
            name=f"{EMOJIS['SHIELD']} Модератор",
            value=interaction.user.mention,
            inline=True
        )
        clear_embed.add_field(
            name=f"{EMOJIS['WARNING']} Снято предупреждений",
            value=f"`{warnings_before}`",
            inline=True
        )
        clear_embed.add_field(
            name=f"{EMOJIS['MESSAGE']} Личное сообщение",
            value=f"{'✅ Отправлено' if dm_sent else '❌ Не удалось отправить'}",
            inline=False
        )

        await interaction.edit_original_response(embed=clear_embed)

async def setup(bot):
    await bot.add_cog(Warn(bot))