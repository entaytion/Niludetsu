from discord import app_commands
from discord.ext import commands
from Niludetsu import EconomyManager, EconomyEmbed, Emojis
from Niludetsu.locale import _

class Bank(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.economy = EconomyManager()

    @commands.hybrid_command(name="deposit", aliases=("dep",), description="Внести деньги в банк")
    @app_commands.describe(amount="Сумма")
    async def deposit(self, ctx, amount: str):
        uid, gid = str(ctx.author.id), str(ctx.guild.id)
        t = _(ctx=ctx)
        
        val = int(amount) if amount.isdigit() else 0
        if val <= 0: return await ctx.reply(t("economy", "invalid_amount"), ephemeral=True)

        res = await self.economy.deposit_money(uid, gid, val)
        if not res:
            return await ctx.reply(embed=EconomyEmbed.error(res.message), ephemeral=True)

        acc = res.data
        embed = EconomyEmbed.result(action=t("economy", "bank_title_deposit"), user=ctx.author, text=t("economy", "bank_deposit_result", amount=f"{val:,}", currency=Emojis.MONEY, wallet=f"{acc['balance']:,}", bank=f"{acc['deposit']:,}"))
        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(name="withdraw", aliases=("wd",), description="Снять деньги из банка")
    @app_commands.describe(amount="Сумма")
    async def withdraw(self, ctx, amount: str):
        uid, gid = str(ctx.author.id), str(ctx.guild.id)
        t = _(ctx=ctx)
        
        val = int(amount) if amount.isdigit() else 0
        if val <= 0: return await ctx.reply(t("economy", "invalid_amount"), ephemeral=True)

        res = await self.economy.withdraw_money(uid, gid, val)
        if not res:
            return await ctx.reply(embed=EconomyEmbed.error(res.message), ephemeral=True)

        acc = res.data
        embed = EconomyEmbed.result(action=t("economy", "bank_title_withdraw"), user=ctx.author, text=t("economy", "bank_withdraw_result", amount=f"{val:,}", currency=Emojis.MONEY, wallet=f"{acc['balance']:,}", bank=f"{acc['deposit']:,}"))
        await ctx.reply(embed=embed, mention_author=False)

async def setup(bot):
    await bot.add_cog(Bank(bot))
