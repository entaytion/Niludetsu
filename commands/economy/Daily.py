from discord.ext import commands
from Niludetsu import EconomyManager, EconomyEmbed, Emojis
from Niludetsu.locale import _

class Daily(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.economy = EconomyManager()

    @commands.hybrid_command(name="daily", description="Получить ежедневную награду")
    async def daily(self, ctx):
        uid, gid = str(ctx.author.id), str(ctx.guild.id)
        t = _(ctx=ctx)
        
        cd = await self.economy.check_cooldown(uid, gid, "daily")
        if cd.status == "cooldown":
            return await ctx.reply(embed=EconomyEmbed.error(t("economy", "daily_cooldown", time=cd.message)), ephemeral=True)

        reward = 250
        await self.economy.add_money(uid, gid, reward, event="daily")
        await self.economy.update_cooldown(uid, gid, "daily")

        embed = EconomyEmbed.result(
            action=t("economy", "daily_title"),
            user=ctx.author,
            text=t("economy", "daily_success", amount=f"{reward:,}", currency=Emojis.MONEY),
        )
        await ctx.reply(embed=embed, mention_author=False)

async def setup(bot):
    await bot.add_cog(Daily(bot))
