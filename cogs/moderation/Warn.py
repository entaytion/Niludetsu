import discord
from discord.ext import commands
from discord import app_commands
import yaml
import sqlite3
from datetime import datetime, timedelta
from utils import create_embed, initialize_table, TABLES_SCHEMAS
import traceback

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
    @has_mod_role()
    async def warn_add(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        reason: str = "Причина не указана"
    ):
        try:
            if user.id == interaction.user.id:
                return await interaction.response.send_message(
                    embed=create_embed(
                        description="Вы не можете выдать предупреждение самому себе!"
                    )
                )

            if user.bot:
                return await interaction.response.send_message(
                    embed=create_embed(
                        description="Нельзя выдать предупреждение боту!"
                    )
                )

            if user.guild_permissions.administrator:
                return await interaction.response.send_message(
                    embed=create_embed(
                        description="Нельзя выдать предупреждение администратору!"
                    )
                )

            await interaction.response.defer()

            cursor = self.db.cursor()
            cursor.execute(
                "INSERT INTO warnings (user_id, guild_id, moderator_id, reason) VALUES (?, ?, ?, ?)",
                (user.id, interaction.guild.id, interaction.user.id, reason)
            )
            self.db.commit()

            warning_count = self.get_user_active_warnings(user.id, interaction.guild.id)

            dm_embed = create_embed(
                title="⚠️ Предупреждение",
                description=(
                    f"Вы получили предупреждение на сервере **{interaction.guild.name}**\n\n"
                    f"**Причина:** {reason}\n"
                    f"**Модератор:** {interaction.user.mention}\n"
                    f"**Количество предупреждений:** **`{warning_count}/{MAX_WARNINGS}`**"
                )
            )

            dm_sent = False
            try:
                await user.send(embed=dm_embed)
                dm_sent = True
            except discord.Forbidden:
                pass
            except Exception as e:
                print(f"Error sending DM: {e}")

            channel_embed = create_embed(
                title="⚠️ Предупреждение выдано",
                description=(
                    f"**Пользователь:** {user.mention} | (ID: {user.id})\n"
                    f"**Модератор:** {interaction.user.mention}\n"
                    f"**Причина:** {reason}\n"
                    f"**Количество предупреждений:** **`{warning_count}/{MAX_WARNINGS}`**\n"
                    f"**Личное сообщение:** {'✅ Отправлено' if dm_sent else '❌ Не удалось отправить'}"
                )
            )

            await interaction.followup.send(embed=channel_embed)

        except Exception as e:
            traceback.print_exc()
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    embed=create_embed(
                        description=f"Произошла ошибка: {str(e)}"
                    )
                )
            else:
                await interaction.followup.send(
                    embed=create_embed(
                        description=f"Произошла ошибка: {str(e)}"
                    )
                )

    @app_commands.command(name="remove", description="Удалить предупреждение у пользователя")
    @app_commands.describe(
        user="Пользователь",
        warning_id="ID предупреждения для удаления"
    )
    @has_mod_role()
    async def warn_remove(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        warning_id: int
    ):
        try:
            cursor = self.db.cursor()
            
            # Проверяем, существует ли предупреждение
            cursor.execute(
                "SELECT * FROM warnings WHERE id = ? AND user_id = ? AND guild_id = ? AND active = TRUE",
                (warning_id, user.id, interaction.guild.id)
            )
            warning = cursor.fetchone()
            
            if not warning:
                return await interaction.response.send_message(
                    embed=create_embed(
                        description="Предупреждение не найдено!"
                    )
                )

            # Деактивируем предупреждение
            cursor.execute(
                "UPDATE warnings SET active = FALSE WHERE id = ?",
                (warning_id,)
            )
            self.db.commit()

            # Попытка отправить сообщение пользователю
            try:
                await user.send(
                    embed=create_embed(
                        title="✅ Предупреждение снято",
                        description=f"С вас снято предупреждение на сервере {interaction.guild.name}\n"
                                  f"**Модератор:** {interaction.user.mention}"
                    )
                )
                dm_sent = True
            except:
                dm_sent = False

            warning_count = self.get_user_active_warnings(user.id, interaction.guild.id)
            
            await interaction.response.send_message(
                embed=create_embed(
                    title="✅ Предупреждение удалено",
                    description=f"Пользователь: {user.mention} | (ID: {user.id})\n"
                              f"**Модератор:** {interaction.user.mention}\n"
                              f"**Оставшиеся предупреждения:** **`{warning_count}/{MAX_WARNINGS}`**\n"
                              f"**Личное сообщение:** {'✅ Отправлено' if dm_sent else '❌ Не удалось отправить'}"
                )
            )
            
        except Exception as e:
            traceback.print_exc()
            await interaction.response.send_message(
                embed=create_embed(
                    description=f"Произошла ошибка: {str(e)}"
                )
            )

    @app_commands.command(name="clear", description="Удалить все предупреждения у пользователя")
    @app_commands.describe(user="Пользователь для очистки предупреждений")
    @has_mod_role()
    async def warn_clear(
        self,
        interaction: discord.Interaction,
        user: discord.Member
    ):
        try:
            cursor = self.db.cursor()
            
            # Деактивируем все предупреждения
            cursor.execute(
                "UPDATE warnings SET active = FALSE WHERE user_id = ? AND guild_id = ? AND active = TRUE",
                (user.id, interaction.guild.id)
            )
            self.db.commit()

            # Попытка отправить сообщение пользователю
            try:
                await user.send(
                    embed=create_embed(
                        title="✅ Предупреждения сняты",
                        description=f"С вас сняты все предупреждения на сервере {interaction.guild.name}\n"
                                  f"**Модератор:** {interaction.user.mention}"
                    )
                )
                dm_sent = True
            except:
                dm_sent = False

            await interaction.response.send_message(
                embed=create_embed(
                    title="✅ Предупреждения очищены",
                    description=f"**Пользователь:** {user.mention} | (ID: {user.id})\n"
                              f"**Модератор:** {interaction.user.mention}\n"
                              f"**Личное сообщение:** {'✅ Отправлено' if dm_sent else '❌ Не удалось отправить'}"
                )
            )
        except Exception as e:
            traceback.print_exc()
            await interaction.response.send_message(
                embed=create_embed(
                    description=f"Произошла ошибка: {str(e)}"
                )
            )

async def setup(bot):
    await bot.add_cog(Warn(bot))