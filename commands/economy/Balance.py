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
    async def balance(self, ctx: commands.Context, user: discord.Member = None):
        if hasattr(ctx, "interaction") and ctx.interaction:
            await ctx.defer()
        target = user or ctx.author
        acc = await self.economy.get_account(str(target.id), str(ctx.guild.id))

        embed = EconomyEmbed.balance(
            user=target,
            wallet=acc.get("balance", 0),
            bank=acc.get("deposit", 0),
            family=acc.get("spousal_balance", 0) if acc.get("spousal_enabled") else None,
        )
        if hasattr(ctx, "interaction") and ctx.interaction and ctx.interaction.response.is_done():
            await ctx.interaction.followup.send(embed=embed)
        else:
            await ctx.reply(embed=embed, mention_author=False)

async def setup(bot):
    await bot.add_cog(Balance(bot))
