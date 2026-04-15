from discord import app_commands
from discord.ext import commands

from Niludetsu import Emojis
from Niludetsu.database.supabase_database import database
from Niludetsu.economy.checks import CheckCooldown
from Niludetsu.economy.manager import EconomyManager
from Niludetsu.embeds.Economy import EconomyEmbed
from Niludetsu.tools.Validator import economy

DAILY_DEFAULT_AMOUNT = 250


class Daily(commands.Cog):
    """Команда для получения ежедневной награды."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = database
        self.economy = EconomyManager(self.db)

    @commands.hybrid_command(
        name="daily", aliases=("timely",), description="💰 Получить ежедневную награду"
    )
    @app_commands.describe()
    @economy(CheckCooldown("daily"))
    async def daily(self, ctx: commands.Context) -> None:
        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)
        reward = DAILY_DEFAULT_AMOUNT

        await self.economy.add_money(user_id, guild_id, reward, event="daily")
        await self.economy.update_cooldown(user_id, guild_id, "daily")

        embed = EconomyEmbed.result(
            action="Ежедневная награда",
            user=ctx.author,
            text=f"вы получили **{reward:,}** {Emojis.MONEY}! До следующей награды — 24 часа.",
        )
        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Daily(bot))
