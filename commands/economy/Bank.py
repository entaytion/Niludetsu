from discord import app_commands
from discord.ext import commands
from Niludetsu import EconomyManager, EconomyEmbed, Emojis

class Bank(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.economy = EconomyManager()

    @commands.hybrid_command(name="deposit", aliases=("dep",), description="Внести деньги в банк")
    @app_commands.describe(amount="Сумма")
    async def deposit(self, ctx, amount: str):
        uid, gid = str(ctx.author.id), str(ctx.guild.id)
        
        # Простой парсинг без лишних декораторов для чистоты
        val = int(amount) if amount.isdigit() else 0
        if val <= 0: return await ctx.reply("Сумма должна быть больше 0", ephemeral=True)

        res = await self.economy.deposit_money(uid, gid, val)
        if not res:
            return await ctx.reply(embed=EconomyEmbed.error(res.message), ephemeral=True)

        acc = res.data
        embed = EconomyEmbed.result(action="Депозит", user=ctx.author, text=f"внесено **{val:,}** {Emojis.MONEY}.\n**Кошелёк:** {acc['balance']:,} | **Банк:** {acc['deposit']:,}")
        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(name="withdraw", aliases=("wd",), description="Снять деньги из банка")
    @app_commands.describe(amount="Сумма")
    async def withdraw(self, ctx, amount: str):
        uid, gid = str(ctx.author.id), str(ctx.guild.id)
        val = int(amount) if amount.isdigit() else 0
        if val <= 0: return await ctx.reply("Сумма должна быть больше 0", ephemeral=True)

        res = await self.economy.withdraw_money(uid, gid, val)
        if not res:
            return await ctx.reply(embed=EconomyEmbed.error(res.message), ephemeral=True)

        acc = res.data
        embed = EconomyEmbed.result(action="Снятие", user=ctx.author, text=f"снято **{val:,}** {Emojis.MONEY}.\n**Кошелёк:** {acc['balance']:,} | **Банк:** {acc['deposit']:,}")
        await ctx.reply(embed=embed, mention_author=False)

async def setup(bot):
    await bot.add_cog(Bank(bot))
