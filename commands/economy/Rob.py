import discord, random
from discord import app_commands
from discord.ext import commands
from Niludetsu import Embed, Colors
from Niludetsu.database.supabase_database import database
from Niludetsu.economy.manager import EconomyManager

ROB_SUCCESS_CHANCE = 0.5

class Rob(commands.Cog):
    """Ограбление с кулдауном."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = database
        self.economy = EconomyManager(self.db)

    @commands.hybrid_command(name="rob", description="🏧 Попробовать ограбить другого пользователя")
    @app_commands.describe(member="👤 Кого ограбить")
    async def rob(self, ctx: commands.Context, member: discord.Member) -> None:
        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)
        target_id = str(member.id)

        if member == ctx.author:
            await ctx.reply(
                embed=Embed.error("Самого себя ограбить нельзя — неудобно и некрасиво."),
                ephemeral=True,
            )
            return

        if member.bot:
            await ctx.reply(
                embed=Embed.error("Ботов грабить бессмысленно — у них нет кошелька."),
                ephemeral=True,
            )
            return

        can_use, error_msg = await self.economy.check_cooldown(user_id, guild_id, "rob")

        if not can_use:
            await ctx.reply(
                embed=Embed.error(description=f"Ты только что провернул дельце! {error_msg}"),
                ephemeral=True,
            )
            return

        victim_wallet = await self.economy.get_wallet(target_id, guild_id)
        if victim_wallet <= 0:
            await ctx.reply(
                embed=Embed.error(description=f"У {member.display_name} в кошельке пусто. Всё лежит в банке — не подлезешь."),
                ephemeral=True,
            )
            return

        await self.economy.update_cooldown(user_id, guild_id, "rob")

        if random.random() <= ROB_SUCCESS_CHANCE:
            max_grab = max(1, int(victim_wallet * 0.35))
            steal_amount = min(victim_wallet, random.randint(1, max_grab))

            removed, remove_msg = await self.economy.remove_money(target_id, guild_id, steal_amount)
            if not removed:
                await ctx.reply(embed=Embed.error(description=remove_msg), ephemeral=True)
                return

            await self.economy.add_money(user_id, guild_id, steal_amount, share_spousal=True)

            embed = Embed(
                title="🕶️ Ограбление удалось!",
                description=(
                    f"Ты стащил {self.economy.format_money(steal_amount)} из кошелька {member.mention}. "
                    "Банк остался неприступным."
                ),
                color=Colors.SUCCESS,
            )
            embed.set_thumbnail(url=ctx.author.display_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)

        else:
            thief_wallet = await self.economy.get_wallet(user_id, guild_id)
            penalty = min(thief_wallet, random.randint(50, 150))
            if penalty > 0:
                await self.economy.remove_money(user_id, guild_id, penalty)

            embed = Embed(
                title="🚨 Пойман с поличным!",
                description=(
                    "Стража оказалась быстрее. "
                    f"Ты выплатил штраф в {self.economy.format_money(penalty)}."
                ),
                color=Colors.ERROR,
            )
            embed.set_thumbnail(url=ctx.author.display_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Rob(bot))

