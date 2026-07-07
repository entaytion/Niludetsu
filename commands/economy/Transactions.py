import discord
from discord import app_commands
from discord.ext import commands
from Niludetsu import Embed, EconomyEmbed, Time, database
from Niludetsu.locale import _

class Transactions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = database
        self.time = Time()

    @commands.hybrid_command(name="transactions", aliases=("tx",), description="Показать историю транзакций")
    async def transactions(self, ctx, user: discord.Member = None):
        t = _(ctx=ctx)
        target = user or ctx.author
        uid, gid = str(target.id), str(ctx.guild.id)

        rows, total = await self.db.get_transactions(uid, gid, limit=10)
        
        if not rows:
            return await ctx.reply(t("economy", "transactions_empty_msg"), ephemeral=True)

        embed = EconomyEmbed.transactions_page(
            display_name=target.display_name,
            rows=rows,
            time_svc=self.time,
            page=0, total=total, page_size=10,
            avatar_url=target.display_avatar.url
        )
        await ctx.reply(embed=embed, mention_author=False)

async def setup(bot): await bot.add_cog(Transactions(bot))
