import discord
from discord import app_commands
from discord.ext import commands
from Niludetsu import (
    Embed,
    Emojis,
    mod_only,
    cooldown
)

class MassRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="massrole", description="Выдать/забрать роль у всех участников")
    @app_commands.describe(
        action="Действие с ролью (add/remove)",
        role="Роль для выдачи/удаления",
        reason="Причина выдачи/удаления роли"
    )
    @mod_only()
    @cooldown(seconds=3)
    async def massrole(
        self,
        interaction: discord.Interaction,
        action: str,
        role: discord.Role,
        reason: str = "Причина не указана"
    ):
        try:
            if not interaction.user.guild_permissions.manage_roles:
                return await interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.ERROR} Ошибка прав",
                        description="У вас нет прав на управление ролями!",
                        color="RED"
                    ),
                    ephemeral=True
                )

            if role >= interaction.guild.me.top_role:
                return await interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.ERROR} Ошибка прав",
                        description="Я не могу управлять этой ролью, так как она выше или равна моей высшей роли!",
                        color="RED"
                    ),
                    ephemeral=True
                )

            if action.lower() not in ['add', 'remove']:
                return await interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.ERROR} Ошибка параметра",
                        description="Действие должно быть 'add' или 'remove'!",
                        color="RED"
                    ),
                    ephemeral=True
                )

            # Отправляем начальное сообщение о процессе
            progress_embed=Embed(
                title=f"{Emojis.LOADING} Обработка ролей",
                description=f"{'Выдаю' if action.lower() == 'add' else 'Удаляю'} роль {role.mention} всем участникам...",
                color="YELLOW"
            )
            await interaction.response.send_message(embed=progress_embed)

            success_count = 0
            failed_count = 0
            skipped_count = 0

            for member in interaction.guild.members:
                if member.bot:
                    skipped_count += 1
                    continue

                try:
                    if action.lower() == 'add':
                        if role not in member.roles:
                            await member.add_roles(role, reason=f"Массовая выдача ролей от {interaction.user} по причине: {reason}")
                            success_count += 1
                        else:
                            skipped_count += 1
                    else:
                        if role in member.roles:
                            await member.remove_roles(role, reason=f"Массовое удаление ролей от {interaction.user} по причине: {reason}")
                            success_count += 1
                        else:
                            skipped_count += 1
                except:
                    failed_count += 1

            # Создаем эмбед с результатами
            result_embed=Embed(
                title=f"{Emojis.SUCCESS} Обработка ролей завершена",
                color="GREEN"
            )

            result_embed.add_field(
                name=f"{Emojis.ROLE} Роль",
                value=role.mention,
                inline=True
            )
            result_embed.add_field(
                name=f"{Emojis.SHIELD} Модератор",
                value=interaction.user.mention,
                inline=True
            )
            result_embed.add_field(
                name=f"{Emojis.SETTINGS} Действие",
                value=f"{'Выдача' if action.lower() == 'add' else 'Удаление'}",
                inline=True
            )
            result_embed.add_field(
                name=f"{Emojis.SUCCESS} Успешно обработано",
                value=f"`{success_count}` участников",
                inline=True
            )
            if failed_count > 0:
                result_embed.add_field(
                    name=f"{Emojis.ERROR} Ошибки",
                    value=f"`{failed_count}` участников",
                    inline=True
                )
            if skipped_count > 0:
                result_embed.add_field(
                    name=f"{Emojis.INFO} Пропущено",
                    value=f"`{skipped_count}` участников",
                    inline=True
                )

            result_embed.set_footer(text=f"ID роли: {role.id}")
            await interaction.edit_original_response(embed=result_embed)

        except discord.Forbidden:
            error_embed=Embed(
                title=f"{Emojis.ERROR} Ошибка прав",
                description="У меня недостаточно прав для управления ролями!",
                color="RED"
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=error_embed)
            else:
                await interaction.edit_original_response(embed=error_embed)

async def setup(bot):
    await bot.add_cog(MassRole(bot))