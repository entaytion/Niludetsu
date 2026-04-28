import discord
from discord import app_commands
from discord.ext import commands
from Niludetsu.moderation.checks import moderationcommand
from Niludetsu import send, ModerationManager, TimeService
from Niludetsu.tools.SendHybrid import send_moderation

from typing import Optional, Union

_time = TimeService()

class BanSystemCog(commands.Cog):
    """Команды управления банами."""

    def __init__(self, bot):
        self.bot = bot
        self.mod_manager = ModerationManager(bot)

    @commands.hybrid_command(name="ban", description="Забанить пользователя (софтбан)")
    @moderationcommand(required_level=3, cooldown=5)
    async def ban(self, ctx, member: discord.Member, reason: str = "Не указана", duration: Optional[str] = None):
        minutes = None
        if duration:
            seconds, _, error = _time.validate(duration, max_days=28, min_seconds=60)
            if error:
                return await send(ctx, error, ephemeral=True)
            minutes = seconds // 60
        res = await self.mod_manager.ban(ctx.guild, member, ctx.author, reason, minutes)
        await send_moderation(ctx, embed=res["embed"])

    @commands.command(name="realban")
    @moderationcommand(required_level=5, cooldown=5)
    async def realban(self, ctx, member: Union[discord.Member, discord.User, int], *, reason: str = "Не указана"):
        if isinstance(member, int): member = discord.Object(id=member)
        res = await self.mod_manager.ban(ctx.guild, member, ctx.author, reason, real=True)
        await send_moderation(ctx, embed=res["embed"])

    @commands.hybrid_command(name="unban", description="Разбанить пользователя")
    @moderationcommand(required_level=3, cooldown=5)
    async def unban(self, ctx, member: discord.Member, *, reason: str = "Не указана"):
        res = await self.mod_manager.unban(ctx.guild, member, ctx.author, reason)
        await send_moderation(ctx, embed=res["embed"])

async def setup(bot):
    await bot.add_cog(BanSystemCog(bot))
