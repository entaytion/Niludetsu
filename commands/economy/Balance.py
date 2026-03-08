import discord
from discord import app_commands
from discord.ext import commands
from Niludetsu.database.supabase_database import database
from Niludetsu.economy.manager import EconomyManager
from Niludetsu.embeds.Economy import EconomyEmbed


class Balance(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = database
        self.economy = EconomyManager(self.db)

    @commands.hybrid_command(name="balance", aliases=("баланс", "b"), description="👛 Показать баланс пользователя")
    @app_commands.describe(user="👤 Кого посмотреть (по умолчанию — вы)")
    async def balance(self, ctx: commands.Context, user: discord.Member | None = None) -> None:
        if ctx.interaction and not ctx.interaction.response.is_done():
            await ctx.defer()
        target = user or ctx.author

        await self.db.ensure_user(str(target.id), str(ctx.guild.id))
        wallet = await self.economy.get_wallet(str(target.id), str(ctx.guild.id))
        bank = await self.economy.get_bank(str(target.id), str(ctx.guild.id))
        family = await self.economy.get_spousal_balance(str(target.id), str(ctx.guild.id))

        rewards_info = None
        if target == ctx.author:
            rewards_info = await self.economy.get_rewards_info(str(target.id), str(ctx.guild.id))

        embed = EconomyEmbed.balance(
            user=target,
            wallet=wallet,
            bank=bank,
            family=family if family else None,
            rewards_info=rewards_info,
        )
        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Balance(bot))
