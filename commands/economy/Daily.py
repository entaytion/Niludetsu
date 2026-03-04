from discord import app_commands
from discord.ext import commands
from Niludetsu import Embed, Colors, Emojis
from Niludetsu.database.supabase_database import database
from Niludetsu.economy.manager import EconomyManager

DAILY_DEFAULT_AMOUNT = 250

class Daily(commands.Cog):
    """Команда для получения ежедневной награды."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = database
        self.economy = EconomyManager(self.db)

    @commands.hybrid_command(name="daily", aliases=("timely",), description="💰 Получить ежедневную награду")
    @app_commands.describe()
    async def daily(self, ctx: commands.Context) -> None:
        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)
        reward = DAILY_DEFAULT_AMOUNT

        can_use, error_msg = await self.economy.check_cooldown(user_id, guild_id, "daily")

        if not can_use:
            embed = Embed.error(
                description=f"Вы уже забирали ежедневку! {error_msg}",
            )
            await ctx.reply(embed=embed, ephemeral=True)
            return

        # Начисляем награду
        await self.economy.add_money(user_id, guild_id, reward)
        await self.economy.update_cooldown(user_id, guild_id, "daily")

        embed = Embed(
            title="💰 Ежедневная награда",
            description=f"Вы получили **{reward:,}** {Emojis.MONEY}! До следующей награды — 24 часа.",
            color=Colors.SUCCESS,
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        await ctx.reply(embed=embed, mention_author=False)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Daily(bot))

