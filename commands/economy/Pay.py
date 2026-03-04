import discord
from discord import app_commands
from discord.ext import commands
from Niludetsu import Embed, Colors
from Niludetsu.database.supabase_database import database
from Niludetsu.economy.manager import EconomyManager
from Niludetsu.economy.validators import EconomyValidator

class Pay(commands.Cog):
    """Перевод денег между пользователями."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = database
        self.economy = EconomyManager(self.db)
        self.validator = EconomyValidator(self.economy)

    @commands.hybrid_command(
        name="pay",
        description="💸 Перевести деньги другому пользователю",
    )
    @app_commands.describe(
        member="👤 Кому отправляем",
        amount="🪙 Сколько монет перевести",
    )
    async def pay(self, ctx: commands.Context, member: discord.Member, amount: str) -> None:
        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)
        target_id = str(member.id)

        ok_amount, amount_value, error_msg = self.validator.parse_amount(amount)
        if not ok_amount:
            await ctx.reply(embed=Embed.error(description=error_msg), ephemeral=True)
            return

        ok_transfer, error_msg = await self.validator.validate_transfer(
            user_id,
            target_id,
            guild_id,
            amount_value,
            bot=self.bot,
        )
        if not ok_transfer:
            await ctx.reply(embed=Embed.error(description=error_msg), ephemeral=True)
            return

        success, message = await self.economy.transfer_money(user_id, target_id, guild_id, amount_value)
        if not success:
            await ctx.reply(embed=Embed.error(description=message), ephemeral=True)
            return

        sender_balance = await self.economy.get_wallet(user_id, guild_id)
        receiver_balance = await self.economy.get_wallet(target_id, guild_id)

        embed = Embed(
            title="💸 Перевод выполнен",
            description=f"Вы отправили {self.economy.format_money(amount_value)} пользователю {member.mention}.",
            color=Colors.SUCCESS,
        )
        embed.add_field(name="Ваш кошелёк", value=self.economy.format_money(sender_balance), inline=True)
        embed.add_field(
            name=f"Кошелёк {member.display_name}",
            value=self.economy.format_money(receiver_balance),
            inline=True,
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        await ctx.reply(embed=embed, mention_author=False)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Pay(bot))

