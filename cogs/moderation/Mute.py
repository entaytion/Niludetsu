import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from datetime import datetime, timedelta
import asyncio
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.emojis import EMOJIS
from Niludetsu.utils.decorators import command_cooldown, has_mod_role

class Mute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.muted_users = {}

    @app_commands.command(name="mute", description="Замутить участника")
    @app_commands.describe(
        member="Участник для мута",
        duration="Длительность мута (например: 1h, 30m, 1d)",
        reason="Причина мута"
    )
    @has_mod_role()
    @command_cooldown()
    async def mute(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        duration: str,
        reason: Optional[str] = None
    ):
        if not interaction.user.guild_permissions.moderate_members:
            return await interaction.response.send_message(
                embed=Embed(
                    title=f"{EMOJIS['ERROR']} Ошибка прав",
                    description="У вас нет прав на управление мутами участников!",
                    color="RED"
                ),
                ephemeral=True
            )

        if member.top_role >= interaction.user.top_role:
            return await interaction.response.send_message(
                embed=Embed(
                    title=f"{EMOJIS['ERROR']} Ошибка прав",
                    description="Вы не можете замутить участника с ролью выше или равной вашей!",
                    color="RED"
                ),
                ephemeral=True
            )

        # Парсим длительность
        try:
            duration_seconds = 0
            time_str = ""
            if duration.endswith('s'):
                duration_seconds = int(duration[:-1])
                time_str = f"{duration_seconds} секунд"
            elif duration.endswith('m'):
                duration_seconds = int(duration[:-1]) * 60
                time_str = f"{int(duration[:-1])} минут"
            elif duration.endswith('h'):
                duration_seconds = int(duration[:-1]) * 3600
                time_str = f"{int(duration[:-1])} часов"
            elif duration.endswith('d'):
                duration_seconds = int(duration[:-1]) * 86400
                time_str = f"{int(duration[:-1])} дней"
            else:
                raise ValueError()

            if duration_seconds <= 0:
                raise ValueError()

        except ValueError:
            return await interaction.response.send_message(
                embed=Embed(
                    title=f"{EMOJIS['ERROR']} Ошибка формата",
                    description="Неверный формат длительности! Используйте: 30s, 5m, 2h, 1d",
                    color="RED"
                ),
                ephemeral=True
            )

        # Проверяем, не замучен ли уже участник
        if member.id in self.muted_users:
            return await interaction.response.send_message(
                embed=Embed(
                    title=f"{EMOJIS['ERROR']} Ошибка",
                    description=f"Участник {member.mention} уже замучен!",
                    color="RED"
                ),
                ephemeral=True
            )

        end_time = datetime.utcnow() + timedelta(seconds=duration_seconds)
        
        # Отправляем сообщение о начале мута
        progress_embed=Embed(
            title=f"{EMOJIS['LOADING']} Применение мута",
            description=f"Применяю мут для {member.mention}...",
            color="YELLOW"
        )
        await interaction.response.send_message(embed=progress_embed)

        try:
            await member.timeout(
                until=end_time,
                reason=f"Мут от {interaction.user}: {reason if reason else 'Причина не указана'}"
            )
            self.muted_users[member.id] = end_time

            # Создаем эмбед с информацией о муте
            mute_embed=Embed(
                title=f"{EMOJIS['MUTE']} Участник замучен",
                color="RED"
            )

            mute_embed.add_field(
                name=f"{EMOJIS['USER']} Участник",
                value=f"{member.mention} (`{member.id}`)",
                inline=True
            )
            mute_embed.add_field(
                name=f"{EMOJIS['SHIELD']} Модератор",
                value=interaction.user.mention,
                inline=True
            )
            mute_embed.add_field(
                name=f"{EMOJIS['TIME']} Длительность",
                value=time_str,
                inline=True
            )
            if reason:
                mute_embed.add_field(
                    name=f"{EMOJIS['REASON']} Причина",
                    value=f"```{reason}```",
                    inline=False
                )

            mute_embed.set_footer(text=f"Мут истекает: {end_time.strftime('%d.%m.%Y %H:%M:%S')} UTC")
            await interaction.edit_original_response(embed=mute_embed)

            # Отправляем уведомление участнику
            try:
                await member.send(
                    embed=Embed(
                        title=f"{EMOJIS['MUTE']} Вы получили мут",
                        description=(
                            f"**Сервер:** {interaction.guild.name}\n"
                            f"**Модератор:** {interaction.user.mention}\n"
                            f"**Длительность:** {time_str}\n"
                            f"**Причина:** {reason if reason else 'Не указана'}\n"
                            f"**Истекает:** {end_time.strftime('%d.%m.%Y %H:%M:%S')} UTC"
                        ),
                        color="RED"
                    )
                )
            except discord.Forbidden:
                pass

            # Запускаем таймер для автоматического размута
            self.bot.loop.create_task(self.unmute_task(interaction.guild, member, duration_seconds))

        except discord.Forbidden:
            await interaction.edit_original_response(
                embed=Embed(
                    title=f"{EMOJIS['ERROR']} Ошибка прав",
                    description="У меня недостаточно прав для мута участников!",
                    color="RED"
                )
            )

    async def unmute_task(self, guild: discord.Guild, member: discord.Member, duration: int):
        await asyncio.sleep(duration)
        if member.id in self.muted_users:
            try:
                await member.timeout(None, reason="Истек срок мута")
                del self.muted_users[member.id]
                
                # Отправляем уведомление участнику
                try:
                    await member.send(
                        embed=Embed(
                            title=f"{EMOJIS['SUCCESS']} Мут снят",
                            description=f"Ваш мут на сервере {guild.name} был автоматически снят.",
                            color="GREEN"
                        )
                    )
                except discord.Forbidden:
                    pass
                
            except discord.NotFound:
                pass  # Участник покинул сервер
            except discord.Forbidden:
                pass  # Недостаточно прав

async def setup(bot):
    await bot.add_cog(Mute(bot))