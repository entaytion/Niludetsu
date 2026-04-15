import discord
from discord import app_commands
from discord.ext import commands
from Niludetsu import Emojis
from Niludetsu.database.supabase_database import database
from Niludetsu.economy.manager import EconomyManager
from Niludetsu.economy.checks import ParseAmount, NotSelf, NotBot, EnsureBalance
from Niludetsu.tools.Validator import economy
from Niludetsu.embeds.Economy import EconomyEmbed


class Pay(commands.Cog):
    """Перевод денег между пользователями."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = database
        self.economy = EconomyManager(self.db)

    @commands.hybrid_command(
        name="pay",
        description="💸 Перевести деньги другому пользователю",
    )
    @app_commands.describe(
        member="👤 Кому отправляем",
        amount="🪙 Сколько монет перевести",
    )
    @economy(
        ParseAmount("amount"),
        NotSelf("Нельзя переводить самому себе"),
        NotBot("Нельзя переводить ботам"),
        EnsureBalance(),
    )
    async def pay(self, ctx: commands.Context, member: discord.Member, amount: str) -> None:
        amount_value: int = ctx.eco["amount"]
        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)
        target_id = str(member.id)

        success, message = await self.economy.transfer_money(user_id, target_id, guild_id, amount_value, event="pay")
        if not success:
            await ctx.reply(embed=EconomyEmbed.error(message), ephemeral=True)
            return

        embed = EconomyEmbed.result(
            action="Перевод",
            user=ctx.author,
            text=f"вы отправили **{amount_value:,}** {Emojis.MONEY} пользователю {member.mention}.",
        )
        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Pay(bot))
