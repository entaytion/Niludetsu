import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from datetime import datetime, timedelta
import asyncio
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.constants import Emojis
from Niludetsu.utils.decorators import command_cooldown, has_mod_role
from Niludetsu.moderation.punishments import Punishment

class Mute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.punishment_handler = Punishment(bot)
        self.muted_users = {}

    @app_commands.command(name="mute", description="Замутить участника")
    @app_commands.describe(
        member="Участник для мута",
        duration="Длительность мута (1h, 1d, 1w)",
        reason="Причина мута"
    )
    @has_mod_role()
    async def mute_slash(self, interaction: discord.Interaction, member: discord.Member, duration: str, reason: str = "Не указана"):
        await self._mute_member(interaction, member, duration, reason)
        
    async def _mute_member(self, ctx, member: discord.Member, duration: str, reason: str):
        """Общая логика мута участника"""
        # Проверяем права
        if member.top_role >= ctx.guild.me.top_role:
            embed = Embed(
                title=f"{Emojis.ERROR} Ошибка",
                description="Я не могу замутить участника с ролью выше моей",
                color="RED"
            )
            if isinstance(ctx, discord.Interaction):
                return await ctx.response.send_message(embed=embed, ephemeral=True)
            return await ctx.send(embed=embed)
            
        # Парсим длительность
        try:
            duration_seconds = self._parse_duration(duration)
            if duration_seconds <= 0:
                raise ValueError("Длительность должна быть положительным числом")
        except ValueError as e:
            embed = Embed(
                title=f"{Emojis.ERROR} Ошибка",
                description=str(e),
                color="RED"
            )
            if isinstance(ctx, discord.Interaction):
                return await ctx.response.send_message(embed=embed, ephemeral=True)
            return await ctx.send(embed=embed)
            
        # Применяем мут
        expires_at = datetime.datetime.now() + datetime.timedelta(seconds=duration_seconds)
        success = await self.punishment_handler.apply_punishment(
            member,
            "mute",
            reason,
            moderator_id=ctx.user.id if isinstance(ctx, discord.Interaction) else ctx.author.id,
            expires_at=expires_at
        )
        
        if success:
            embed = Embed(
                title=f"{Emojis.SUCCESS} Участник замучен",
                description=(
                    f"{Emojis.DOT} **Участник:** {member.mention}\n"
                    f"{Emojis.DOT} **Длительность:** {duration}\n"
                    f"{Emojis.DOT} **Причина:** {reason}\n"
                    f"{Emojis.DOT} **Истекает:** <t:{int(expires_at.timestamp())}:R>"
                ),
                color="GREEN"
            )
        else:
            embed = Embed(
                title=f"{Emojis.ERROR} Ошибка",
                description="Не удалось замутить участника",
                color="RED"
            )
            
        if isinstance(ctx, discord.Interaction):
            await ctx.response.send_message(embed=embed)
        else:
            await ctx.send(embed=embed)
            
    def _parse_duration(self, duration: str) -> int:
        """Парсит строку длительности в секунды"""
        try:
            value = int(duration[:-1])
            unit = duration[-1].lower()
            
            if unit == 's':
                return value
            elif unit == 'm':
                return value * 60
            elif unit == 'h':
                return value * 3600
            elif unit == 'd':
                return value * 86400
            elif unit == 'w':
                return value * 604800
            else:
                raise ValueError("Неверный формат длительности. Используйте s/m/h/d/w (секунды/минуты/часы/дни/недели)")
        except (IndexError, ValueError):
            raise ValueError("Неверный формат длительности. Пример: 1h, 1d, 1w")

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
                            title=f"{Emojis.SUCCESS} Мут снят",
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