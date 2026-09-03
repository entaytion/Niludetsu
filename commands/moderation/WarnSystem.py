import discord
from discord import app_commands
from discord.ext import commands
from Niludetsu.moderation.checks import moderationcommand
from Niludetsu import send, ModerationManager, Embed, TimeService
from Niludetsu.tools.SendHybrid import send_moderation
from Niludetsu.locale import _

from typing import Optional

_time = TimeService()

class WarnSystemCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.mod_manager = ModerationManager(bot)

    @commands.hybrid_command(name="warn", description="Выдать предупреждение пользователю")
    @app_commands.describe(user="👤 Пользователь", reason="💬 Причина", duration="⏰ Длительность (напр: 30m, 2h)")
    @moderationcommand(required_level=2, cooldown=5)
    async def warn(self, ctx, user: discord.Member, reason: str, duration: Optional[str] = None):
        minutes = None
        if duration:
            seconds, _, error = _time.validate(duration, max_days=28, min_seconds=60)
            if error:
                return await send(ctx, error, ephemeral=True)
            minutes = seconds // 60
        res = await self.mod_manager.warn(ctx.guild, user, ctx.author, reason, minutes)
        await send_moderation(ctx, embed=res["embed"])

    @commands.hybrid_command(name="unwarn", description="Снять предупреждение")
    @app_commands.describe(user="👤 Пользователь", warn_id="🆔 ID варна", reason="💬 Причина")
    @moderationcommand(required_level=1, cooldown=5)
    async def unwarn(self, ctx, user: discord.Member, warn_id: str, *, reason: Optional[str] = None):
        t = _(ctx=ctx)
        if reason is None: reason = t("moderation", "reason_default")
        res = await self.mod_manager.unwarn(ctx.guild, user, ctx.author, reason, rudiment=warn_id)
        await send_moderation(ctx, embed=res["embed"])

async def setup(bot):
    await bot.add_cog(WarnSystemCog(bot))
