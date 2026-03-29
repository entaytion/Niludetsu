import random

import discord
from discord import app_commands
from discord.ext import commands

from Niludetsu import Emojis
from Niludetsu.database.supabase_database import database
from Niludetsu.economy.checks import CheckCooldown, NotBot, NotSelf
from Niludetsu.economy.manager import EconomyManager
from Niludetsu.embeds.Economy import EconomyEmbed
from Niludetsu.tools.Validator import economy

ROB_SUCCESS_CHANCE = 0.5


class Rob(commands.Cog):
    """Ограбление с кулдауном."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = database
        self.economy = EconomyManager(self.db)

    @commands.hybrid_command(
        name="rob", description="🏧 Попробовать ограбить другого пользователя"
    )
    @app_commands.describe(member="👤 Кого ограбить")
    @economy(
        NotSelf("Самого себя ограбить нельзя — неудобно и некрасиво."),
        NotBot("Ботов грабить бессмысленно — у них нет кошелька."),
        CheckCooldown("rob"),
    )
    async def rob(self, ctx: commands.Context, member: discord.Member) -> None:
        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)
        target_id = str(member.id)

        victim_wallet = await self.economy.get_wallet(target_id, guild_id)
        if victim_wallet <= 0:
            await ctx.reply(
                embed=EconomyEmbed.error(
                    f"У {member.display_name} в кошельке пусто. Всё лежит в банке — не подлезешь."
                ),
                ephemeral=True,
            )
            return

        await self.economy.update_cooldown(user_id, guild_id, "rob")

        if random.random() <= ROB_SUCCESS_CHANCE:
            max_grab = max(1, int(victim_wallet * 0.35))
            steal_amount = min(victim_wallet, random.randint(1, max_grab))

            removed, remove_msg = await self.economy.remove_money(
                target_id, guild_id, steal_amount, event="rob", related_user_id=user_id
            )
            if not removed:
                await ctx.reply(embed=EconomyEmbed.error(remove_msg), ephemeral=True)
                return

            await self.economy.add_money(
                user_id,
                guild_id,
                steal_amount,
                share_spousal=True,
                event="rob",
                related_user_id=target_id,
            )

            embed = EconomyEmbed.result(
                action="Ограбление",
                user=ctx.author,
                text=f"вы **успешно ограбили** {member.mention} и украли **{steal_amount:,}** {Emojis.MONEY} из кошелька.",
            )
            await ctx.reply(embed=embed, mention_author=False)

        else:
            thief_wallet = await self.economy.get_wallet(user_id, guild_id)
            penalty = min(thief_wallet, random.randint(50, 150))
            if penalty > 0:
                await self.economy.remove_money(
                    user_id, guild_id, penalty, event="rob_penalty"
                )

            wallet = await self.economy.get_wallet(user_id, guild_id)

            embed = EconomyEmbed.result(
                action="Ограбление",
                user=ctx.author,
                text=(
                    f"стража оказалась быстрее. "
                    f"Вы выплатили штраф в **{penalty:,}** {Emojis.MONEY}."
                ),
                balance=wallet,
            )
            await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Rob(bot))
