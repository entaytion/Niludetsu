import discord
from discord import app_commands
from discord.ext import commands
from Niludetsu.moderation.checks import moderationcommand
from Niludetsu.moderation.exceptions import ModerationError
from Niludetsu import send
from Niludetsu.tools.SendHybrid import send_moderation, ensure_embed
from Niludetsu.moderation.system.ban import BanSystem
from Niludetsu.tools.Embed import Embed
from Niludetsu.tools.Time import TimeService
from typing import Optional, Union

_time = TimeService()



class BanSystemCog(commands.Cog):
    """Команды управления банами."""

    def __init__(self, bot):
        self.bot = bot
        self.ban_system = BanSystem(bot)

    @commands.hybrid_command(
        name="ban",
        description="🛡️ Забанить пользователя (софтбан через роль)"
    )
    @app_commands.describe(
        member="👤 Пользователь для бана",
        reason="💬 Причина бана",
        duration="⏰ Длительность (например: 1d, 30d, 1h30m)"
    )
    @moderationcommand(required_level=3, cooldown=1800)
    async def ban(
        self,
        ctx: commands.Context,
        member: discord.Member,
        reason: str = "Не указана",
        duration: Optional[str] = None
    ):
        """
        Забанить пользователя (софтбан через роль).

        Примеры:
        • !ban @user Спам
        • !ban @user Флуд 1d
        • !ban @user "Реклама Discord серверов" 30d
        • /ban member:@user reason:Спам duration:1d
        """
        duration_minutes = None
        if duration:
            try:
                parsed_duration = _time.parse_duration(duration)
                if parsed_duration:
                    duration_minutes = int(parsed_duration.total_seconds() / 60)
                else:
                    raise ValueError("Не удалось распарсить длительность")
            except Exception as e:
                embed = Embed.error(
                    title="❌ Неверный формат длительности",
                    description=(
                        f"Не удалось распарсить длительность: `{duration}`\n"
                        "**Примеры правильного формата:**\n`30s` — 30 секунд, `5m` — 5 минут, `2h` — 2 часа, `7d` — 7 дней, `1w` — 1 неделя"
                    )
                )
                return await send(ctx, embed=embed, ephemeral=True)

        result = await self.ban_system.ban(
            guild=ctx.guild,
            user=member,
            moderator=ctx.author,
            reason=reason,
            duration=duration_minutes,
            channel=ctx.channel,
            real=False  # Софтбан
        )

        await send_moderation(ctx, embed=ensure_embed(result))

    @commands.command(
        name="realban",
        description="Забанить пользователя навсегда (настоящий бан через Discord API)"
    )
    @moderationcommand(required_level=5, cooldown=1800)  # Уровень 5 - только администраторы
    async def realban(
        self,
        ctx: commands.Context,
        member: Union[discord.Member, discord.User, int],
        *,
        reason: str = "Не указана"
    ):
        """
        Настоящий бан через Discord API (только префиксная команда).
        Доступно только для Администраторов (уровень 5).
        Можно банить ботов и пользователей по ID, которых нет на сервере.

        Примеры:
        • !realban @user Нарушение правил сервера
        • !realban @bot Спам-бот
        • !realban 950455573357424640 Нарушение правил (по ID)
        """
        # Если передан ID, создаем объект discord.Object для бана
        if isinstance(member, int):
            user_obj = discord.Object(id=member)
        else:
            user_obj = member

        try:
            result = await self.ban_system.ban(
                guild=ctx.guild,
                user=user_obj,
                moderator=ctx.author,
                reason=reason,
                channel=ctx.channel,
                real=True  # Настоящий бан
            )

            await send_moderation(ctx, embed=ensure_embed(result))
        except Exception as e:
            error_embed = Embed.error(description=str(e))
            await ctx.send(embed=error_embed)

    @commands.hybrid_command(
        name="unban",
        description="🛡️ Разбанить пользователя"
    )
    @app_commands.describe(
        member="👤 Пользователь для разбана",
        reason="💬 Причина разбана"
    )
    @moderationcommand(required_level=3, cooldown=1800)
    async def unban(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: str = "Не указана"
    ):
        """
        Разбанить пользователя.

        Примеры:
        • !unban @user Апелляция принята
        • /unban member:@user reason:Истёк срок
        """
        result = await self.ban_system.unban(
            guild=ctx.guild,
            user=member,
            moderator=ctx.author,
            reason=reason,
            channel=ctx.channel
        )

        await send_moderation(ctx, embed=ensure_embed(result))

async def setup(bot):
    await bot.add_cog(BanSystemCog(bot))

