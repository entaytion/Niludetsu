import discord
from Niludetsu import Embed, LevelManager
from Niludetsu.locale import _
from discord import app_commands
from discord.ext import commands

from typing import Optional

class LevelCard(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.levels = LevelManager()

    def generate_progress_bar(self, current: int, required: int, length: int = 15) -> str:
        if required <= 0: return "🟩" * length
        filled = int((current / required) * length)
        filled = min(max(filled, 0), length)
        empty = length - filled
        return f"[{'🟩' * filled}{'⬛' * empty}]"

    @commands.hybrid_command(
        name="level", aliases=["ранг", "уровень"], description="Показать уровень пользователя"
    )
    @app_commands.describe(user="👤 Пользователь (по умолчанию — вы)")
    async def level_cmd(self, ctx: commands.Context, user: Optional[discord.Member] = None) -> None:
        if ctx.interaction and not ctx.interaction.response.is_done():
            await ctx.interaction.response.defer(thinking=True)

        t = _(ctx=ctx)

        target = user or ctx.author
        if target.bot:
            return await ctx.reply(f"❌ {t('profile', 'level_bot_error')}", ephemeral=True)

        profile = await self.levels.get_profile(str(ctx.guild.id), str(target.id))

        lvl = profile["level"]
        exp = profile["experience"]
        req_exp = self.levels.next_level_xp(lvl)

        progress_bar = self.generate_progress_bar(exp, req_exp)
        percent = int((exp / req_exp) * 100) if req_exp > 0 else 100

        embed = Embed.default(title=t("profile", "level_title", user_name=target.display_name))
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name=t("profile", "level_rank"), value=f"🏆 **{lvl}**", inline=True)
        embed.add_field(name=t("profile", "level_xp"), value=f"✨ **{exp:,}** / {req_exp:,}", inline=True)
        embed.add_field(name=t("profile", "level_progress"), value=f"{progress_bar} **{percent}%**", inline=False)

        await ctx.reply(embed=embed, mention_author=False)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(LevelCard(bot))
