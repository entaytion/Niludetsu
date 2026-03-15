import discord
from discord import app_commands
from discord.ext import commands
from Niludetsu.moderation.checks import moderationcommand
from Niludetsu import send
from Niludetsu.tools.SendHybrid import ensure_embed, send_moderation
from Niludetsu.moderation.system.mute import MuteSystem as NiludetsuMuteSystem
from Niludetsu.tools.Embed import Embed
from Niludetsu.tools.Time import TimeService

_time = TimeService()

class MuteSystem(commands.Cog):
    """Команды управления мутами через Discord Timeout."""

    def __init__(self, bot):
        self.bot = bot
        self.mute_system = NiludetsuMuteSystem(bot)

    @commands.hybrid_command(
        name="mute",
        description="🛡️ Выдать мут пользователю (Discord Timeout)"
    )
    @app_commands.describe(
        member="👤 Пользователь для мута",
        duration="⏰ Длительность (например: 1h, 30m, 1d)",
        reason="💬 Причина мута"
    )
    @moderationcommand(required_level=1, cooldown=1800)
    async def mute(
        self,
        ctx: commands.Context,
        member: discord.Member,
        duration: str,
        *,
        reason: str = "Не указана"
    ):
        """
        Замютить пользователя (Discord Timeout).

        Примеры:
        • !mute @user Спам
        • !mute @user Флуд 1d
        • !mute @user "Реклама Discord серверов" 30d
        • /mute member:@user reason:Спам duration:1d
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

        result = await self.mute_system.mute(
            guild=ctx.guild,
            user=member,
            moderator=ctx.author,
            duration=duration_minutes,
            reason=reason,
            channel=ctx.channel
        )

        await send_moderation(ctx, embed=ensure_embed(result))

    @commands.hybrid_command(
        name="unmute",
        description="🛡️ Снять мут с пользователя"
    )
    @app_commands.describe(
        member="👤 Пользователь для размута",
        reason="💬 Причина размута"
    )
    @moderationcommand(required_level=1, cooldown=1800)
    async def unmute(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: str = "Не указана"
    ):
        """
        Снять мут с пользователя.

        Примеры:
        • !unmute @user Апелляция принята
        • /unmute member:@user reason:Ошибочный мут
        """
        result = await self.mute_system.unmute(
            guild=ctx.guild,
            user=member,
            moderator=ctx.author,
            reason=reason,
            channel=ctx.channel
        )

        await send_moderation(ctx, embed=ensure_embed(result))

async def setup(bot):
    await bot.add_cog(MuteSystem(bot))

