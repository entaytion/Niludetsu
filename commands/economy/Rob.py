import random
import discord
from discord.ext import commands
from Niludetsu import EconomyManager, EconomyEmbed, Emojis, Colors

class Rob(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.economy = EconomyManager()

    @commands.hybrid_command(name="rob", description="Попробовать ограбить пользователя")
    async def rob(self, ctx, user: discord.Member):
        if user.id == ctx.author.id: return await ctx.reply("Себя нельзя!", ephemeral=True)
        if user.bot: return await ctx.reply("Ботов нельзя!", ephemeral=True)

        uid, gid, tid = str(ctx.author.id), str(ctx.guild.id), str(user.id)
        
        cd = await self.economy.check_cooldown(uid, gid, "rob")
        if cd.status == "cooldown":
            return await ctx.reply(embed=EconomyEmbed.error(f"Полиция всё еще ищет вас! Приходите через **{cd.message}**."), ephemeral=True)

        author_acc = await self.economy.get_account(uid, gid)
        target_acc = await self.economy.get_account(tid, gid)

        if author_acc["balance"] < 500:
            return await ctx.reply("Нужно иметь хотя бы 500 монет, чтобы пойти на дело.", ephemeral=True)
        if target_acc["balance"] < 100:
            return await ctx.reply("У жертвы нечего брать.", ephemeral=True)

        await self.economy.update_cooldown(uid, gid, "rob")

        if random.random() <= 0.45:
            percent = random.randint(10, 40)
            amount = int(target_acc["balance"] * (percent / 100))
            await self.economy.transfer_money(tid, uid, gid, amount, event="rob")
            text = f"Ограбление удалось! 🔫\nВы вытащили **{amount:,}** {Emojis.MONEY} у {user.mention}."
            color = Colors.SUCCESS
        else:
            penalty = int(author_acc["balance"] * 0.2)
            await self.economy.remove_money(uid, gid, penalty, event="rob_penalty")
            text = f"Вас поймали! 👮\nВы заплатили штраф **{penalty:,}** {Emojis.MONEY}."
            color = Colors.ERROR

        await ctx.reply(embed=EconomyEmbed.result(action="Ограбление", user=ctx.author, text=text, color=color))

async def setup(bot): await bot.add_cog(Rob(bot))
