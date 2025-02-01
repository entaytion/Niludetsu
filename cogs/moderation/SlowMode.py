import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.emojis import EMOJIS
from Niludetsu.utils.decorators import command_cooldown, has_mod_role

class Slowmode(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="slowmode", description="Установить медленный режим в канале")
    @app_commands.describe(
        seconds="Задержка в секундах (0-21600, 0 для отключения)",
        channel="Канал для установки медленного режима (по умолчанию - текущий)",
        reason="Причина изменения медленного режима"
    )
    @has_mod_role()
    @command_cooldown()
    async def slowmode(
        self,
        interaction: discord.Interaction,
        seconds: app_commands.Range[int, 0, 21600],
        channel: Optional[discord.TextChannel] = None,
        reason: Optional[str] = None
    ):
        if not interaction.user.guild_permissions.manage_channels:
            return await interaction.response.send_message(
                embed=Embed(
                    title=f"{EMOJIS['ERROR']} Ошибка прав",
                    description="У вас нет прав на управление каналами!",
                    color="RED"
                ),
                ephemeral=True
            )

        target_channel = channel or interaction.channel

        # Отправляем начальное сообщение
        progress_embed=Embed(
            title=f"{EMOJIS['LOADING']} Изменение медленного режима",
            description=f"Устанавливаю задержку в канале {target_channel.mention}...",
            color="YELLOW"
        )
        await interaction.response.send_message(embed=progress_embed)

        # Форматируем время для отображения
        if seconds == 0:
            time_str = "отключен"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            time_parts = []
            
            if hours > 0:
                time_parts.append(f"{hours}ч")
            if minutes > 0:
                time_parts.append(f"{minutes}м")
            if secs > 0 or not time_parts:
                time_parts.append(f"{secs}с")
            
            time_str = " ".join(time_parts)

        try:
            await target_channel.edit(
                slowmode_delay=seconds,
                reason=f"Медленный режим изменен {interaction.user}: {reason if reason else 'Причина не указана'}"
            )

            # Создаем эмбед с результатами
            result_embed=Embed(
                title=f"{EMOJIS['SUCCESS']} Медленный режим изменен",
                color="GREEN"
            )

            result_embed.add_field(
                name=f"{EMOJIS['CHANNEL']} Канал",
                value=target_channel.mention,
                inline=True
            )
            result_embed.add_field(
                name=f"{EMOJIS['SHIELD']} Модератор",
                value=interaction.user.mention,
                inline=True
            )
            result_embed.add_field(
                name=f"{EMOJIS['TIME']} Задержка",
                value=time_str,
                inline=True
            )

            if reason:
                result_embed.add_field(
                    name=f"{EMOJIS['REASON']} Причина",
                    value=f"```{reason}```",
                    inline=False
                )

            result_embed.set_footer(text=f"ID канала: {target_channel.id}")
            await interaction.edit_original_response(embed=result_embed)

            # Отправляем уведомление в канал
            try:
                await target_channel.send(
                    embed=Embed(
                        title=f"{EMOJIS['INFO']} Медленный режим изменен",
                        description=(
                            f"**Модератор:** {interaction.user.mention}\n"
                            f"**Новая задержка:** {time_str}\n"
                            f"**Причина:** {reason if reason else 'Не указана'}"
                        ),
                        color="BLUE"
                    )
                )
            except discord.Forbidden:
                pass

        except discord.Forbidden:
            await interaction.edit_original_response(
                embed=Embed(
                    title=f"{EMOJIS['ERROR']} Ошибка прав",
                    description=f"У меня недостаточно прав для изменения настроек канала {target_channel.mention}!",
                    color="RED"
                )
            )

async def setup(bot):
    await bot.add_cog(Slowmode(bot))    