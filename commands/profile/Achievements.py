import discord
from discord import app_commands
from discord.ext import commands
from Niludetsu import Embed, Colors, Time, AchievementsManager
from Niludetsu.locale import _

_time = Time()

class AchievementsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.manager = AchievementsManager()

    @commands.hybrid_command(name="achievements", description="⭐ Посмотреть свои достижения")
    @app_commands.describe(member="👤 Чьи достижения показать (по умолчанию — ваши)")
    async def achievements(self, ctx: commands.Context, member: discord.Member | None = None) -> None:
        t = _(ctx=ctx)
        target = member or ctx.author
        guild_id = str(ctx.guild.id)
        user_id = str(target.id)

        summary = await self.manager.get_user_summary(guild_id, user_id)
        total = sum(1 for item in summary.values() if item["unlocked"])

        embed = Embed.user(
            user=target,
            title=t("profile", "achievements_title", user_name=target.display_name),
            description=f"> {t('profile', 'achievements_unlocked', unlocked=total, total=len(summary))}",
            color=Colors.SUCCESS,
        )
        for ach_id, data in summary.items():
            status = t("profile", "achievements_status_unlocked" if data["unlocked"] else "achievements_status_locked")
            line = f"{status} {data['icon']} **{data['name']}** — {data['description']}"
            if data["unlocked_at"]:
                line += f"\n{t('profile', 'achievements_received')} {_time.format_datetime(data['unlocked_at'])}"
            embed.add_field(name=data.get("category", "").capitalize(), value=line, inline=False)
        await ctx.reply(embed=embed, mention_author=False)

    async def award_marriage(self, guild_id: str, user_id: str, channel: discord.TextChannel | None = None):
        await self.manager.unlock(guild_id, user_id, "first_marriage", channel=channel)

async def setup(bot: commands.Bot):
    await bot.add_cog(AchievementsCog(bot))
