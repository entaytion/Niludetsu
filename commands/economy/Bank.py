from discord import app_commands
from discord.ext import commands
from Niludetsu import Embed, Colors
from Niludetsu.database.supabase_database import database
from Niludetsu.economy.manager import EconomyManager
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
    async def deposit(self, ctx: commands.Context, amount: Optional[int] = None) -> None:
        if amount is None or amount <= 0:
            await ctx.reply(
                embed=Embed.error("Укажите положительную сумму, чтобы внести в банк."),
                ephemeral=True,
            )
            return

        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)

        success, message = await self.economy.deposit_money(user_id, guild_id, amount)

        if not success:
            await ctx.reply(embed=Embed.error(message), ephemeral=True)
            return

        wallet = await self.economy.get_wallet(user_id, guild_id)
        bank = await self.economy.get_bank(user_id, guild_id)

        embed = Embed(
            title="🏦 Депозит выполнен",
            description=message,
            color=Colors.SUCCESS,
        )
        embed.add_field(name="Кошелёк", value=self.economy.format_money(wallet), inline=True)
        embed.add_field(name="Банк", value=self.economy.format_money(bank), inline=True)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(
        name="withdraw",
        aliases=("wd", "вывод"),
        description="🏧 Снять деньги с банковского счёта",
    )
    @app_commands.describe(amount="Сумма, которую хотите вернуть из банка")
    async def withdraw(self, ctx: commands.Context, amount: Optional[int] = None) -> None:
        if amount is None or amount <= 0:
            await ctx.reply(
                embed=Embed.error("Укажите положительную сумму, чтобы снять с депозита."),
                ephemeral=True,
            )
            return

        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)

        success, message = await self.economy.withdraw_money(user_id, guild_id, amount)

        if not success:
            await ctx.reply(embed=Embed.error(message), ephemeral=True)
            return

        wallet = await self.economy.get_wallet(user_id, guild_id)
        bank = await self.economy.get_bank(user_id, guild_id)

        embed = Embed(
            title="🏧 Снятие выполнено",
            description=message,
            color=Colors.SUCCESS,
        )
        embed.add_field(name="Кошелёк", value=self.economy.format_money(wallet), inline=True)
        embed.add_field(name="Банк", value=self.economy.format_money(bank), inline=True)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(
        name="withdrawfamily",
        aliases=("wdf", "familywithdraw"),
        description="💍 Снять деньги с семейного счёта",
    )
    @app_commands.describe(amount="Сумма для снятия (оставьте пустым, чтобы забрать всё)")
    async def withdraw_family(self, ctx: commands.Context, amount: Optional[int] = None) -> None:
        if amount is not None and amount <= 0:
            await ctx.reply(
                embed=Embed.error("Сумма должна быть положительной."),
                ephemeral=True,
            )
            return

        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)

        success, result_embed = await self.economy.withdraw_spousal(user_id, guild_id, amount)

        if not success:
            await ctx.reply(embed=result_embed, ephemeral=True)
            return

        wallet = await self.economy.get_wallet(user_id, guild_id)
        family = await self.economy.get_spousal_balance(user_id, guild_id)

        result_embed.title = "💍 Семейный баланс обновлён"
        result_embed.color = Colors.SUCCESS
        result_embed.add_field(name="Кошелёк", value=self.economy.format_money(wallet), inline=True)
        result_embed.add_field(name="Семейный счёт", value=self.economy.format_money(family), inline=True)
        await ctx.reply(embed=result_embed, mention_author=False)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Bank(bot))

