import discord
from discord import app_commands
from discord.ext import commands
from Niludetsu import EconomyManager, EconomyEmbed, Emojis

class Balance(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.economy = EconomyManager()

    @commands.hybrid_command(name="balance", aliases=("баланс", "b"), description="Показать баланс")
    @app_commands.describe(user="👤 Кого посмотреть")
    async def balance(self, ctx, user: discord.Member = None):
        target = user or ctx.author
        acc = await self.economy.get_account(str(target.id), str(ctx.guild.id))

        embed = EconomyEmbed.balance(
            user=target,
            wallet=acc["balance"],
            bank=acc["deposit"],
            family=acc["spousal_balance"] if acc.get("spousal_enabled") else None
        )
        await ctx.reply(embed=embed, mention_author=False)

async def setup(bot):
    await bot.add_cog(Balance(bot))
