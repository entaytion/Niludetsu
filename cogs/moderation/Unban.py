import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from Niludetsu.utils.embed import create_embed
from Niludetsu.core.base import EMOJIS
from Niludetsu.utils.decorators import command_cooldown, has_mod_role

class Unban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="unban", description="Разбанить участника")
    @app_commands.describe(
        user="ID пользователя для разбана",
        reason="Причина разбана"
    )
    @has_mod_role()
    @command_cooldown()
    async def unban(
        self,
        interaction: discord.Interaction,
        user: str,
        reason: Optional[str] = None
    ):
        try:
            if not interaction.user.guild_permissions.ban_members:
                return await interaction.response.send_message(
                    embed=create_embed(
                        title=f"{EMOJIS['ERROR']} Ошибка прав",
                        description="У вас нет прав на управление банами!",
                        color="RED"
                    ),
                    ephemeral=True
                )

            # Отправляем начальное сообщение
            progress_embed = create_embed(
                title=f"{EMOJIS['LOADING']} Разбан участника",
                description=f"Выполняю разбан участника с ID: `{user}`...",
                color="YELLOW"
            )
            await interaction.response.send_message(embed=progress_embed)

            try:
                # Пытаемся получить информацию о бане
                ban_entry = None
                try:
                    ban_entry = await interaction.guild.fetch_ban(discord.Object(id=int(user)))
                except (ValueError, discord.NotFound):
                    # Если ID неверный или пользователь не забанен
                    return await interaction.edit_original_response(
                        embed=create_embed(
                            title=f"{EMOJIS['ERROR']} Ошибка",
                            description="Пользователь с таким ID не найден в списке забаненных!",
                            color="RED"
                        )
                    )

                # Разбаниваем пользователя
                await interaction.guild.unban(
                    ban_entry.user,
                    reason=f"Разбан от {interaction.user}: {reason if reason else 'Причина не указана'}"
                )

                # Создаем эмбед с результатами
                unban_embed = create_embed(
                    title=f"{EMOJIS['SUCCESS']} Участник разбанен",
                    color="GREEN"
                )

                unban_embed.add_field(
                    name=f"{EMOJIS['USER']} Участник",
                    value=f"{ban_entry.user.mention} (`{ban_entry.user.id}`)",
                    inline=True
                )
                unban_embed.add_field(
                    name=f"{EMOJIS['SHIELD']} Модератор",
                    value=interaction.user.mention,
                    inline=True
                )

                if reason:
                    unban_embed.add_field(
                        name=f"{EMOJIS['REASON']} Причина разбана",
                        value=f"```{reason}```",
                        inline=False
                    )

                if ban_entry.reason:
                    unban_embed.add_field(
                        name=f"{EMOJIS['INFO']} Причина бана",
                        value=f"```{ban_entry.reason}```",
                        inline=False
                    )

                unban_embed.set_footer(text=f"ID пользователя: {ban_entry.user.id}")
                await interaction.edit_original_response(embed=unban_embed)

                # Пытаемся отправить уведомление пользователю
                try:
                    await ban_entry.user.send(
                        embed=create_embed(
                            title=f"{EMOJIS['SUCCESS']} Вы были разбанены",
                            description=(
                                f"**Сервер:** {interaction.guild.name}\n"
                                f"**Модератор:** {interaction.user.mention}\n"
                                f"**Причина:** {reason if reason else 'Не указана'}"
                            ),
                            color="GREEN"
                        )
                    )
                except discord.Forbidden:
                    pass

            except discord.Forbidden:
                await interaction.edit_original_response(
                    embed=create_embed(
                        title=f"{EMOJIS['ERROR']} Ошибка прав",
                        description="У меня недостаточно прав для разбана участников!",
                        color="RED"
                    )
                )
            except Exception as e:
                await interaction.edit_original_response(
                    embed=create_embed(
                        title=f"{EMOJIS['ERROR']} Ошибка",
                        description=f"Произошла ошибка при разбане: {str(e)}",
                        color="RED"
                    )
                )

        except Exception as e:
            error_embed = create_embed(
                title=f"{EMOJIS['ERROR']} Ошибка",
                description=f"Произошла непредвиденная ошибка: {str(e)}",
                color="RED"
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=error_embed)
            else:
                await interaction.edit_original_response(embed=error_embed)

async def setup(bot):
    await bot.add_cog(Unban(bot)) 
    await bot.add_cog(Unban(bot)) 