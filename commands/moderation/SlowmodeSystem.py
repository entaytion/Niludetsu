import discord
from discord import app_commands
from discord.ext import commands
from Niludetsu.moderation.checks import moderationcommand
from Niludetsu import send, Embed, Emojis
from Niludetsu.moderation.system.slowmode import SlowmodeSystem
from Niludetsu.locale import _

from typing import Optional

class SlowmodeCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.slowmode = SlowmodeSystem(bot)

    @commands.hybrid_command(
        name="slowmode",
        description="Установить медленный режим в канале"
    )
    @app_commands.describe(
        duration="⏰ Длительность (например: 10s, 1m, 1h, 0/off)",
        channel="#️⃣ Канал (по умолчанию — текущий)",
        reason="💬 Причина"
    )
    @moderationcommand(required_level=2, cooldown=60)
    async def slowmode(
        self,
        ctx: commands.Context,
        duration: str,
        channel: Optional[discord.TextChannel] = None,
        *,
        reason: str = "Не указана"
    ):
        t = _(ctx=ctx)
        is_interaction = getattr(ctx, 'interaction', None) is not None
        apply_to_all = False

        if not is_interaction:
            if reason and "--all" in reason:
                apply_to_all = True
                reason = reason.replace("--all", "").strip()
                if not reason:
                    reason = t("moderation", "reason_default")

        if channel is None and not apply_to_all:
            channel = ctx.channel

        if apply_to_all:
            success_channels, failed_channels = await self.slowmode.set_slowmode_all(
                guild=ctx.guild,
                moderator=ctx.author,
                duration=duration,
                reason=reason
            )

            if success_channels:
                if failed_channels:
                    description = t("moderation", "slowmode_partial", duration=duration, count=len(success_channels), failed=len(failed_channels))
                else:
                    description = t("moderation", "slowmode_success", duration=duration, count=len(success_channels))
                result_embed = Embed.success(description=description)
            else:
                result_embed = Embed.error(description=t("moderation", "slowmode_failed"))

            await send(ctx, embed=result_embed, ephemeral=True)

        else:
            embed = await self.slowmode.set_slowmode(
                guild=ctx.guild,
                moderator=ctx.author,
                channel=channel,
                duration=duration,
                reason=reason
            )
            await send(ctx, embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(SlowmodeCog(bot))

