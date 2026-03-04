import discord
from discord import app_commands
from discord.ext import commands
from Niludetsu.moderation.checks import moderationcommand
from Niludetsu import send
from Niludetsu.tools.SendHybrid import ensure_embed, send_moderation
from Niludetsu.moderation.system.warn import WarnSystem
from Niludetsu.tools.Embed import Embed
from Niludetsu.tools.Time import TimeService
from typing import Optional

_time = TimeService()

class WarnSystemCog(commands.Cog):
    """Команды системы предупреждений."""

    def __init__(self, bot):
        self.bot = bot
        self.warn_system = WarnSystem(bot)

    @commands.hybrid_command(
        name="warn",
        description="🛡️ Выдать предупреждение пользователю"
    )
    @app_commands.describe(
        user="👤 Пользователь для предупреждения",
        reason="💬 Причина предупреждения",
        duration="⏰ Длительность (например: 30m, 2h, 7d) или пусто для постоянного"
    )
    @moderationcommand(required_level=2, cooldown=5)
    async def warn(
        self,
        ctx: commands.Context,
        user: discord.Member,
        reason: str,
        duration: Optional[str] = None
    ):
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

        result = await self.warn_system.add_warn(
            guild=ctx.guild,
            user=user,
            moderator=ctx.author,
            reason=reason,
            duration=duration_minutes,
            channel=ctx.channel
        )

        await send_moderation(ctx, embed=ensure_embed(result))

    @commands.hybrid_command(
        name="unwarn",
        description="🛡️ Снять предупреждение с пользователя"
    )
    @app_commands.describe(
        user="👤 Пользователь",
        warn_id="🆔 ID предупреждения (например: 1, 2, 3)",
        reason="💬 Причина снятия"
    )
    @moderationcommand(required_level=1, cooldown=1800)
    async def unwarn(
        self,
        ctx: commands.Context,
        user: discord.Member,
        warn_id: str,
        *,
        reason: str = "Не указана"
    ):
        """
        Снять предупреждение с пользователя.

        Примеры:
        • !unwarn @user 1 Апелляция принята
        • !unwarn @user 2 Ошибочное предупреждение
        • /unwarn user:@user warn_id:1 reason:Апелляция
        """
        result = await self.warn_system.remove_warn(
                guild=ctx.guild,
                user=user,
                warn_id=str(warn_id),
                moderator=ctx.author,
                reason=reason,
                channel=ctx.channel
            )
        await send_moderation(ctx, embed=ensure_embed(result))

async def setup(bot):
    await bot.add_cog(WarnSystemCog(bot))

