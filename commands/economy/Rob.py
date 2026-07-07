import random
import discord
from discord.ext import commands
from Niludetsu import EconomyManager, EconomyEmbed, Emojis, Colors
from Niludetsu.locale import _

class Rob(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.economy = EconomyManager()

    @commands.hybrid_command(name="rob", description="Попробовать ограбить пользователя")
    async def rob(self, ctx, user: discord.Member):
        t = _(ctx=ctx)
        if user.id == ctx.author.id: return await ctx.reply(t("economy", "rob_self_error"), ephemeral=True)
        if user.bot: return await ctx.reply(t("economy", "rob_bot_error"), ephemeral=True)

        uid, gid, tid = str(ctx.author.id), str(ctx.guild.id), str(user.id)
        
        cd = await self.economy.check_cooldown(uid, gid, "rob")
        if cd.status == "cooldown":
            return await ctx.reply(embed=EconomyEmbed.error(t("economy", "rob_cooldown", time=cd.message)), ephemeral=True)

        author_acc = await self.economy.get_account(uid, gid)
        target_acc = await self.economy.get_account(tid, gid)

        if author_acc["balance"] < 500:
            return await ctx.reply(t("economy", "rob_min_balance", min_amount="500", currency=Emojis.MONEY), ephemeral=True)
        if target_acc["balance"] < 100:
            return await ctx.reply(t("economy", "rob_target_poor"), ephemeral=True)

        await self.economy.update_cooldown(uid, gid, "rob")

        if random.random() <= 0.45:
            percent = random.randint(10, 40)
            amount = int(target_acc["balance"] * (percent / 100))
            await self.economy.transfer_money(tid, uid, gid, amount, event="rob")
            text = t("economy", "rob_success_text", amount=f"{amount:,}", currency=Emojis.MONEY, target_mention=user.mention)
            color = Colors.SUCCESS
        else:
            penalty = int(author_acc["balance"] * 0.2)
            await self.economy.remove_money(uid, gid, penalty, event="rob_penalty")
            text = t("economy", "rob_fail_text", amount=f"{penalty:,}", currency=Emojis.MONEY)
            color = Colors.ERROR

        await ctx.reply(embed=EconomyEmbed.result(action=t("economy", "rob_title"), user=ctx.author, text=text, color=color))

async def setup(bot): await bot.add_cog(Rob(bot))
