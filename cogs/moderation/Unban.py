import discord
from discord.ext import commands
from discord import app_commands
from utils import create_embed, has_admin_role, command_cooldown
import yaml

# Загрузка конфигурации
CONFIG_FILE = 'config/config.yaml'
with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

class Unban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="unban", description="Разбанить пользователя на сервере")
    @app_commands.describe(
        user_id="ID пользователя для разбана",
        reason="Причина разбана"
    )
    @has_admin_role()
    @command_cooldown()
    async def unban(
        self,
        interaction: discord.Interaction,
        user_id: str,
        reason: str = "Причина не указана"
    ):
        if not interaction.guild.me.guild_permissions.ban_members:
            return await interaction.response.send_message(
                embed=create_embed(
                    description="У бота недостаточно прав для выполнения этого действия!"
                ),
                ephemeral=True
            )

        try:
            # Проверяем, является ли user_id числом
            user_id = int(user_id)
            user = await self.bot.fetch_user(user_id)

            # Проверяем, забанен ли пользователь
            try:
                ban_entry = await interaction.guild.fetch_ban(user)
            except discord.NotFound:
                return await interaction.response.send_message(
                    embed=create_embed(
                        description="Этот пользователь не находится в бане!"
                    ),
                    ephemeral=True
                )

            # Разбаниваем пользователя
            await interaction.guild.unban(user, reason=f"{reason} | Разбанил: {interaction.user}")

            # Пытаемся отправить сообщение пользователю
            try:
                await user.send(
                    embed=create_embed(
                        title="🔓 Разбан",
                        description=f"Вы были разбанены на сервере {interaction.guild.name}\n"
                                  f"**Причина:** `{reason}`\n"
                                  f"**Модератор:** {interaction.user.mention}",
                    )
                )
                dm_sent = True
            except:
                dm_sent = False

            # Отправляем сообщение об успешном разбане
            await interaction.response.send_message(
                embed=create_embed(
                    title="🔓 Разбан",
                    description=f"**Пользователь:** {user.name} | (ID: {user.id})\n"
                              f"**Модератор:** {interaction.user.name} | (ID: {interaction.user.id})\n"
                              f"**Причина:** `{reason}`\n"
                              f"**Личное сообщение:** {'✅ Отправлено' if dm_sent else '❌ Не удалось отправить'}\n"
                              f"**Предыдущая причина бана:** `{ban_entry.reason or 'Не указана'}`"
                )
            )

        except ValueError:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Указан некорректный ID пользователя!"
                ),
                ephemeral=True
            )
        except discord.NotFound:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Пользователь не найден!"
                ),
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Недостаточно прав для разбана!"
                ),
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Unban(bot)) 