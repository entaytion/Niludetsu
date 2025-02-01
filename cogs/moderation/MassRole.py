import discord
from discord import app_commands
from discord.ext import commands
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.emojis import EMOJIS
from Niludetsu.utils.decorators import command_cooldown, has_mod_role

class Massrole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="massrole", description="Выдать/забрать роль у всех участников")
    @app_commands.describe(
        role="Роль для выдачи/удаления",
        action="Действие (add/remove)",
        bots="Включать ботов (True/False)"
    )
    @has_mod_role()
    @command_cooldown()
    async def massrole(
        self,
        interaction: discord.Interaction,
        role: discord.Role,
        action: str,
        bots: bool = False
    ):
        try:
            if not interaction.user.guild_permissions.manage_roles:
                return await interaction.response.send_message(
                    embed=Embed(
                        title=f"{EMOJIS['ERROR']} Ошибка прав",
                        description="У вас нет прав на управление ролями!",
                        color="RED"
                    ),
                    ephemeral=True
                )

            if role >= interaction.guild.me.top_role:
                return await interaction.response.send_message(
                    embed=Embed(
                        title=f"{EMOJIS['ERROR']} Ошибка прав",
                        description="Я не могу управлять этой ролью, так как она выше или равна моей высшей роли!",
                        color="RED"
                    ),
                    ephemeral=True
                )

            if action.lower() not in ['add', 'remove']:
                return await interaction.response.send_message(
                    embed=Embed(
                        title=f"{EMOJIS['ERROR']} Ошибка параметра",
                        description="Действие должно быть 'add' или 'remove'!",
                        color="RED"
                    ),
                    ephemeral=True
                )

            # Отправляем начальное сообщение о процессе
            progress_embed=Embed(
                title=f"{EMOJIS['LOADING']} Обработка ролей",
                description=f"{'Выдаю' if action.lower() == 'add' else 'Удаляю'} роль {role.mention} всем участникам...",
                color="YELLOW"
            )
            await interaction.response.send_message(embed=progress_embed)

            success_count = 0
            failed_count = 0
            skipped_count = 0

            for member in interaction.guild.members:
                if member.bot and not bots:
                    skipped_count += 1
                    continue

                try:
                    if action.lower() == 'add':
                        if role not in member.roles:
                            await member.add_roles(role, reason=f"Массовая выдача ролей от {interaction.user}")
                            success_count += 1
                        else:
                            skipped_count += 1
                    else:
                        if role in member.roles:
                            await member.remove_roles(role, reason=f"Массовое удаление ролей от {interaction.user}")
                            success_count += 1
                        else:
                            skipped_count += 1
                except:
                    failed_count += 1

            # Создаем эмбед с результатами
            result_embed=Embed(
                title=f"{EMOJIS['SUCCESS']} Обработка ролей завершена",
                color="GREEN"
            )

            result_embed.add_field(
                name=f"{EMOJIS['ROLE']} Роль",
                value=role.mention,
                inline=True
            )
            result_embed.add_field(
                name=f"{EMOJIS['SHIELD']} Модератор",
                value=interaction.user.mention,
                inline=True
            )
            result_embed.add_field(
                name=f"{EMOJIS['SETTINGS']} Действие",
                value=f"{'Выдача' if action.lower() == 'add' else 'Удаление'}",
                inline=True
            )
            result_embed.add_field(
                name=f"{EMOJIS['SUCCESS']} Успешно обработано",
                value=f"`{success_count}` участников",
                inline=True
            )
            if failed_count > 0:
                result_embed.add_field(
                    name=f"{EMOJIS['ERROR']} Ошибки",
                    value=f"`{failed_count}` участников",
                    inline=True
                )
            if skipped_count > 0:
                result_embed.add_field(
                    name=f"{EMOJIS['INFO']} Пропущено",
                    value=f"`{skipped_count}` участников",
                    inline=True
                )

            result_embed.set_footer(text=f"ID роли: {role.id}")
            await interaction.edit_original_response(embed=result_embed)

        except discord.Forbidden:
            error_embed=Embed(
                title=f"{EMOJIS['ERROR']} Ошибка прав",
                description="У меня недостаточно прав для управления ролями!",
                color="RED"
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=error_embed)
            else:
                await interaction.edit_original_response(embed=error_embed)

async def setup(bot):
    await bot.add_cog(Massrole(bot))