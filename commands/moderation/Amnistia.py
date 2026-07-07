import discord
from discord.ext import commands
from Niludetsu.tools.Embed import Embed
from Niludetsu import send
from Niludetsu.locale import _

class AmnistiaCog(commands.Cog):
    """Команда массового разбана всех забаненных пользователей."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="amnistia")
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(ban_members=True)
    async def amnistia(self, ctx: commands.Context):
        t = _(ctx=ctx)
        bans = [entry async for entry in ctx.guild.bans()]

        if not bans:
            embed = Embed.error(description=t("moderation", "amnistia_no_bans"))
            return await send(ctx, embed=embed)

        progress_embed = Embed.warning(
            title=t("moderation", "amnistia_progress_title"),
            description=t("moderation", "amnistia_progress_desc", count=len(bans))
        )
        msg = await ctx.send(embed=progress_embed)

        unbanned = 0
        failed = 0

        for entry in bans:
            try:
                await ctx.guild.unban(entry.user, reason=t("moderation", "amnistia_reason", moderator=ctx.author))
                unbanned += 1
            except Exception:
                failed += 1

        if failed:
            description = t("moderation", "amnistia_result_partial", unbanned=unbanned, failed=failed)
        else:
            description = t("moderation", "amnistia_result_desc", unbanned=unbanned)

        result_embed = Embed.success(
            title=t("moderation", "amnistia_result_title"),
            description=description
        )
        await msg.edit(embed=result_embed)


async def setup(bot):
    await bot.add_cog(AmnistiaCog(bot))
