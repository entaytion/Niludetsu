import discord
from discord import app_commands
from discord.ext import commands
from Niludetsu import EconomyManager, EconomyEmbed, Emojis

class Pay(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.economy = EconomyManager()

    @commands.hybrid_command(name="pay", description="Перевести деньги")
    @app_commands.describe(member="Кому", amount="Сколько")
    async def pay(self, ctx, member: discord.Member, amount: str):
        if member.id == ctx.author.id: return await ctx.reply("Себе нельзя!", ephemeral=True)
        if member.bot: return await ctx.reply("Ботам нельзя!", ephemeral=True)
        
        val = int(amount) if amount.isdigit() else 0
        if val <= 0: return await ctx.reply("Сумма должна быть больше 0", ephemeral=True)

        res = await self.economy.transfer_money(str(ctx.author.id), str(member.id), str(ctx.guild.id), val)
        if not res:
            return await ctx.reply(embed=EconomyEmbed.error(res.message), ephemeral=True)

        await ctx.reply(embed=EconomyEmbed.result(action="Перевод", user=ctx.author, text=f"вы отправили **{val:,}** {Emojis.MONEY} пользователю {member.mention}."), mention_author=False)

async def setup(bot):
    await bot.add_cog(Pay(bot))
