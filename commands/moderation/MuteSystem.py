import discord
from typing import Optional
from discord import app_commands
from discord.ext import commands
from Niludetsu.moderation.checks import moderationcommand
from Niludetsu import send, ModerationManager, TimeService, Embed
from Niludetsu.tools.SendHybrid import send_moderation
from Niludetsu.locale import _

_time = TimeService()

class MuteSystem(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.mod_manager = ModerationManager(bot)

    @commands.hybrid_command(name="mute", description="Выдать мут пользователю")
    @app_commands.describe(member="👤 Пользователь", duration="⏰ Длительность (напр: 1h, 1d)", reason="💬 Причина")
    @moderationcommand(required_level=1, cooldown=5)
    async def mute(self, ctx, member: discord.Member, duration: str, *, reason: Optional[str] = None):
        t = _(ctx=ctx)
        if reason is None: reason = t("moderation", "reason_default")
        seconds, _, err = _time.validate(duration, max_days=28, min_seconds=60)
        if err: return await send(ctx, embed=Embed.error(description=err), ephemeral=True)
        
        res = await self.mod_manager.mute(ctx.guild, member, ctx.author, seconds // 60, reason)
        await send_moderation(ctx, embed=res["embed"])

    @commands.hybrid_command(name="unmute", description="Снять мут")
    @moderationcommand(required_level=1, cooldown=5)
    async def unmute(self, ctx, member: discord.Member, *, reason: Optional[str] = None):
        t = _(ctx=ctx)
        if reason is None: reason = t("moderation", "reason_default")
        res = await self.mod_manager.unmute(ctx.guild, member, ctx.author, reason)
        await send_moderation(ctx, embed=res["embed"])

async def setup(bot):
    await bot.add_cog(MuteSystem(bot))
