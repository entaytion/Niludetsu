import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu import (
    Embed,
    Emojis,
    mod_only,
    cooldown
)

class Unban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="unban", description="Разбанить пользователя")
    @app_commands.describe(
        user_id="ID пользователя для разбана",
        reason="Причина разбана"
    )
    @mod_only()
    @cooldown(seconds=3)
    async def unban(
        self,
        interaction: discord.Interaction,
        user_id: str,
        reason: str = "Причина не указана"
    ):
        if not interaction.user.guild_permissions.ban_members:
            return await interaction.response.send_message(
                embed=Embed(
                    title=f"{Emojis.ERROR} Ошибка прав",
                    description="У вас нет прав на управление банами!",
                    color="RED"
                ),
                ephemeral=True
            )

        # Отправляем начальное сообщение
        progress_embed=Embed(
            title=f"{Emojis.LOADING} Разбан участника",
            description=f"Выполняю разбан участника с ID: `{user_id}`...",
            color="YELLOW"
        )
        await interaction.response.send_message(embed=progress_embed)

        try:
            # Пытаемся получить информацию о бане
            ban_entry = None
            try:
                ban_entry = await interaction.guild.fetch_ban(discord.Object(id=int(user_id)))
            except (ValueError, discord.NotFound):
                # Если ID неверный или пользователь не забанен
                return await interaction.edit_original_response(
                    embed=Embed(
                        title=f"{Emojis.ERROR} Ошибка",
                        description="Пользователь с таким ID не найден в списке забаненных!",
                        color="RED"
                    )
                )

            # Разбаниваем пользователя
            await interaction.guild.unban(
                ban_entry.user,
                reason=f"Разбан от {interaction.user}: {reason}"
            )

            # Создаем эмбед с результатами
            unban_embed=Embed(
                title=f"{Emojis.SUCCESS} Участник разбанен",
                color="GREEN"
            )

            unban_embed.add_field(
                name=f"{Emojis.USER} Участник",
                value=f"{ban_entry.user.mention} (`{ban_entry.user.id}`)",
                inline=True
            )
            unban_embed.add_field(
                name=f"{Emojis.SHIELD} Модератор",
                value=interaction.user.mention,
                inline=True
            )

            if reason:
                unban_embed.add_field(
                    name=f"{Emojis.REASON} Причина разбана",
                    value=f"```{reason}```",
                    inline=False
                )

            if ban_entry.reason:
                unban_embed.add_field(
                    name=f"{Emojis.INFO} Причина бана",
                    value=f"```{ban_entry.reason}```",
                    inline=False
                )

            unban_embed.set_footer(text=f"ID пользователя: {ban_entry.user.id}")
            await interaction.edit_original_response(embed=unban_embed)

            # Пытаемся отправить уведомление пользователю
            try:
                await ban_entry.user.send(
                    embed=Embed(
                        title=f"{Emojis.SUCCESS} Вы были разбанены",
                        description=(
                            f"**Сервер:** {interaction.guild.name}\n"
                            f"**Модератор:** {interaction.user.mention}\n"
                            f"**Причина:** {reason}"
                        ),
                        color="GREEN"
                    )
                )
            except discord.Forbidden:
                pass

        except discord.Forbidden:
            await interaction.edit_original_response(
                embed=Embed(
                    title=f"{Emojis.ERROR} Ошибка прав",
                    description="У меня недостаточно прав для разбана участников!",
                    color="RED"
                )
            )

async def setup(bot):
    await bot.add_cog(Unban(bot)) 