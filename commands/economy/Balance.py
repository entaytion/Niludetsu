import discord
from discord import app_commands
from discord.ext import commands
from Niludetsu import Embed, Colors
from Niludetsu.database.supabase_database import database
from Niludetsu.economy.manager import EconomyManager
from Niludetsu.economy.validators import EconomyValidator

class Balance(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = database
        self.economy = EconomyManager(self.db)
        self.validator = EconomyValidator(self.economy)

    @commands.hybrid_command(name="balance", aliases=("баланс","b"), description="👛 Показать баланс пользователя")
    @app_commands.describe(user="👤 Кого посмотреть (по умолчанию — вы)")
    async def balance(self, ctx: commands.Context, user: discord.Member | None = None) -> None:
        target = user or ctx.author

        await self.db.ensure_user(str(target.id), str(ctx.guild.id))
        wallet = await self.economy.get_wallet(str(target.id), str(ctx.guild.id))
        bank = await self.economy.get_bank(str(target.id), str(ctx.guild.id))
        family = await self.economy.get_spousal_balance(str(target.id), str(ctx.guild.id))

        embed = Embed(
            title=f"💰 Баланс {target.display_name}",
            color=Colors.SUCCESS,
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="> Кошелёк", value=self.economy.format_money(wallet), inline=True)
        embed.add_field(name="> Банк", value=self.economy.format_money(bank), inline=True)
        if family:
            embed.add_field(name="> Семейный счёт", value=self.economy.format_money(family), inline=False)

        # Добавляем информацию о доступных наградах (только если смотрим свой баланс)
        if target == ctx.author:
            rewards_info = await self.economy.get_rewards_info(str(target.id), str(ctx.guild.id))
            embed.add_field(name="💎 Доступные награды:", value=rewards_info, inline=False)

        await ctx.reply(embed=embed, mention_author=False)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Balance(bot))

