from discord import app_commands
from discord.ext import commands
from Niludetsu import Emojis
from Niludetsu.database.supabase_database import database
from Niludetsu.economy.manager import EconomyManager
from Niludetsu.economy.checks import ParseAmount, EnsureBalance
from Niludetsu.tools.Validator import economy
from Niludetsu.embeds.Economy import EconomyEmbed
from typing import Optional


class Bank(commands.Cog):
    """Команды работы с банковским и семейным счетами."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = database
        self.economy = EconomyManager(self.db)

    @commands.hybrid_command(
        name="deposit",
        aliases=("dep", "депозит"),
        description="🏦 Внести деньги на банковский счёт",
    )
    @app_commands.describe(amount="Сумма, которую хотите отправить в банк")
    @economy(ParseAmount("amount"), EnsureBalance())
    async def deposit(self, ctx: commands.Context, amount: Optional[str] = None) -> None:
        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)
        value = ctx.eco["amount"]

        success, message = await self.economy.deposit_money(user_id, guild_id, value)
        if not success:
            await ctx.reply(embed=EconomyEmbed.error(message), ephemeral=True)
            return

        wallet = await self.economy.get_wallet(user_id, guild_id)
        bank = await self.economy.get_bank(user_id, guild_id)

        embed = EconomyEmbed.result(
            action="Депозит",
            user=ctx.author,
            text=(
                f"вы внесли **{value:,}** {Emojis.MONEY} на банковский счёт.\n"
                f"**Кошелёк:** {wallet:,} {Emojis.MONEY} • **Банк:** {bank:,} {Emojis.MONEY}"
            ),
        )
        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(
        name="withdraw",
        aliases=("wd", "вывод"),
        description="🏧 Снять деньги с банковского счёта",
    )
    @app_commands.describe(amount="Сумма, которую хотите вернуть из банка")
    @economy(ParseAmount("amount"))
    async def withdraw(self, ctx: commands.Context, amount: Optional[str] = None) -> None:
        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)
        value = ctx.eco["amount"]

        success, message = await self.economy.withdraw_money(user_id, guild_id, value)
        if not success:
            await ctx.reply(embed=EconomyEmbed.error(message), ephemeral=True)
            return

        wallet = await self.economy.get_wallet(user_id, guild_id)
        bank = await self.economy.get_bank(user_id, guild_id)

        embed = EconomyEmbed.result(
            action="Снятие",
            user=ctx.author,
            text=(
                f"вы сняли **{value:,}** {Emojis.MONEY} с банковского счёта.\n"
                f"**Кошелёк:** {wallet:,} {Emojis.MONEY} • **Банк:** {bank:,} {Emojis.MONEY}"
            ),
        )
        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(
        name="withdrawfamily",
        aliases=("wdf", "familywithdraw"),
        description="💍 Снять деньги с семейного счёта",
    )
    @app_commands.describe(amount="Сумма для снятия (оставьте пустым, чтобы забрать всё)")
    async def withdraw_family(self, ctx: commands.Context, amount: Optional[int] = None) -> None:
        if ctx.interaction and not ctx.interaction.response.is_done():
            await ctx.defer()
        if amount is not None and amount <= 0:
            await ctx.reply(embed=EconomyEmbed.error("Сумма должна быть положительной."), ephemeral=True)
            return

        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)

        success, result_embed = await self.economy.withdraw_spousal(user_id, guild_id, amount)
        if not success:
            await ctx.reply(embed=result_embed, ephemeral=True)
            return

        wallet = await self.economy.get_wallet(user_id, guild_id)
        family = await self.economy.get_spousal_balance(user_id, guild_id)

        withdrawn = amount or 0
        embed = EconomyEmbed.result(
            action="Семейный счёт",
            user=ctx.author,
            text=(
                f"вы сняли средства с семейного счёта.\n"
                f"**Кошелёк:** {wallet:,} {Emojis.MONEY} • **Семейный:** {family:,} {Emojis.MONEY}"
            ),
        )
        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Bank(bot))
