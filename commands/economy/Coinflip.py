import random
from discord import app_commands
from discord.ext import commands
from Niludetsu import EconomyManager, EconomyEmbed, Emojis, Embed, Colors
from Niludetsu.locale import _

class Coinflip(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.economy = EconomyManager()

    @commands.hybrid_command(name="coinflip", aliases=("cf", "монетка"), description="Подбросить монетку на деньги")
    @app_commands.describe(side="Орел или Решка", bet="Ставка")
    async def coinflip(self, ctx, side: str, bet: str):
        uid, gid = str(ctx.author.id), str(ctx.guild.id)
        t = _(ctx=ctx)
        
        val = int(bet) if bet.isdigit() else 0
        if val <= 0: return await ctx.reply(t("economy", "invalid_bet"), ephemeral=True)
        
        side = side.lower()
        if side not in ("орел", "решка", "о", "р"):
            return await ctx.reply(t("economy", "invalid_side"), ephemeral=True)
        
        res = await self.economy.remove_money(uid, gid, val, event="cf_bet")
        if res.status == "insufficient_funds":
            return await ctx.reply(embed=EconomyEmbed.error(t("economy", "insufficient_funds")), ephemeral=True)
        elif res.status == "error":
            return await ctx.reply(res.message, ephemeral=True)
        
        res_side = random.choice(["орел", "решка"])
        win = (side.startswith(res_side[0]))
        
        if win:
            payout = val * 2
            await self.economy.add_money(uid, gid, payout, event="cf_win")
            text = t("economy", "cf_win", side=res_side.upper(), amount=f"{payout:,}", currency=Emojis.MONEY)
        else:
            text = t("economy", "cf_lose", side=res_side.upper())

        await ctx.reply(embed=EconomyEmbed.result(action=t("economy", "coinflip_title"), user=ctx.author, text=text, color=Colors.SUCCESS if win else Colors.ERROR))

async def setup(bot): await bot.add_cog(Coinflip(bot))
