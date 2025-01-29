import discord
from discord.ext import commands
from discord import app_commands
import yaml
from typing import Optional
from Niludetsu.utils.embed import create_embed
from Niludetsu.utils.emojis import EMOJIS
from Niludetsu.utils.decorators import command_cooldown, has_admin_role

class Reset(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open("config/config.yaml", "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

    @app_commands.command(name="reset", description="Сбросить никнейм и/или аватар участника")
    @app_commands.describe(
        member="Участник для сброса",
        nickname="Сбросить никнейм",
        avatar="Сбросить аватар",
        reason="Причина сброса"
    )
    @has_admin_role()
    @command_cooldown()
    async def reset(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        nickname: Optional[bool] = False,
        avatar: Optional[bool] = False,
        reason: Optional[str] = None
    ):
        if not interaction.user.guild_permissions.manage_nicknames and nickname:
            return await interaction.response.send_message(
                embed=create_embed(
                    title=f"{EMOJIS['ERROR']} Ошибка прав",
                    description="У вас нет прав на управление никнеймами!",
                    color="RED"
                ),
                ephemeral=True
            )

        if not (nickname or avatar):
            return await interaction.response.send_message(
                embed=create_embed(
                    title=f"{EMOJIS['ERROR']} Ошибка параметров",
                    description="Выберите хотя бы одно действие: сброс никнейма или аватара!",
                    color="RED"
                ),
                ephemeral=True
            )

        if member.top_role >= interaction.user.top_role:
            return await interaction.response.send_message(
                embed=create_embed(
                    title=f"{EMOJIS['ERROR']} Ошибка прав",
                    description="Вы не можете сбросить данные участника с ролью выше или равной вашей!",
                    color="RED"
                ),
                ephemeral=True
            )

        # Отправляем начальное сообщение
        progress_embed = create_embed(
            title=f"{EMOJIS['LOADING']} Сброс данных",
            description=f"Сбрасываю данные участника {member.mention}...",
            color="YELLOW"
        )
        await interaction.response.send_message(embed=progress_embed)

        success_actions = []
        failed_actions = []

        # Сброс никнейма
        if nickname and member.nick:
            try:
                await member.edit(
                    nick=None,
                    reason=f"Сброс никнейма от {interaction.user}: {reason if reason else 'Причина не указана'}"
                )
                success_actions.append("никнейм")
            except discord.Forbidden:
                failed_actions.append("никнейм")

        # Сброс аватара (если есть серверный)
        if avatar and member.guild_avatar:
            try:
                await member.edit(
                    avatar=None,
                    reason=f"Сброс аватара от {interaction.user}: {reason if reason else 'Причина не указана'}"
                )
                success_actions.append("аватар")
            except discord.Forbidden:
                failed_actions.append("аватар")

        # Создаем эмбед с результатами
        result_embed = create_embed(
            title=f"{EMOJIS['SUCCESS' if success_actions else 'ERROR']} Сброс данных",
            color="GREEN" if success_actions else "RED"
        )

        result_embed.add_field(
            name=f"{EMOJIS['USER']} Участник",
            value=f"{member.mention} (`{member.id}`)",
            inline=True
        )
        result_embed.add_field(
            name=f"{EMOJIS['SHIELD']} Модератор",
            value=interaction.user.mention,
            inline=True
        )

        if success_actions:
            result_embed.add_field(
                name=f"{EMOJIS['SUCCESS']} Успешно сброшено",
                value=", ".join(success_actions),
                inline=False
            )

        if failed_actions:
            result_embed.add_field(
                name=f"{EMOJIS['ERROR']} Не удалось сбросить",
                value=", ".join(failed_actions),
                inline=False
            )

        if reason:
            result_embed.add_field(
                name=f"{EMOJIS['REASON']} Причина",
                value=f"```{reason}```",
                inline=False
            )

        result_embed.set_footer(text=f"ID участника: {member.id}")
        await interaction.edit_original_response(embed=result_embed)

        # Отправляем уведомление участнику
        try:
            await member.send(
                embed=create_embed(
                    title=f"{EMOJIS['INFO']} Сброс данных",
                    description=(
                        f"**Сервер:** {interaction.guild.name}\n"
                        f"**Модератор:** {interaction.user.mention}\n"
                        f"**Сброшено:** {', '.join(success_actions)}\n"
                        f"**Причина:** {reason if reason else 'Не указана'}"
                    ),
                    color="BLUE"
                )
            )
        except discord.Forbidden:
            pass

async def setup(bot):
    await bot.add_cog(Reset(bot))