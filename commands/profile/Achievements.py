import discord
from discord import app_commands
from discord.ext import commands
from Niludetsu import Embed, Colors, Time
from Niludetsu.achievements.manager import AchievementsManager

_time = Time()

class AchievementsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.manager = AchievementsManager()

    @commands.hybrid_command(name="achievements", description="⭐ Посмотреть свои достижения")
    @app_commands.describe(member="👤 Чьи достижения показать (по умолчанию — ваши)")
    async def achievements(self, ctx: commands.Context, member: discord.Member | None = None) -> None:
        target = member or ctx.author
        guild_id = str(ctx.guild.id)
        user_id = str(target.id)

        summary = await self.manager.get_user_summary(guild_id, user_id)
        total = sum(1 for item in summary.values() if item["unlocked"])

        embed = Embed(
            title=f"⭐ Достижения {target.display_name}",
            description=f"> Разблокировано: **{total}/{len(summary)}**",
            color=Colors.SUCCESS,
        )
        for ach_id, data in summary.items():
            status = "✅" if data["unlocked"] else "❌"
            line = f"{status} {data['icon']} **{data['name']}** — {data['description']}"
            if data["unlocked_at"]:
                line += f"\n• Получено: {_time.format_datetime(data['unlocked_at'])}"
            embed.add_field(name=data["category"].capitalize(), value=line, inline=False)

        embed.set_thumbnail(url=target.display_avatar.url)
        await ctx.reply(embed=embed, mention_author=False)

    async def award_marriage(self, guild_id: str, user_id: str, channel: discord.TextChannel | None = None):
        await self.manager.unlock(guild_id, user_id, "first_marriage", channel=channel)

async def setup(bot: commands.Bot):
    await bot.add_cog(AchievementsCog(bot))

