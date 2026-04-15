import random

from discord.ext import commands

from Niludetsu import Emojis
from Niludetsu.database.supabase_database import database
from Niludetsu.economy.checks import CheckCooldown
from Niludetsu.economy.manager import EconomyManager
from Niludetsu.embeds.Economy import EconomyEmbed
from Niludetsu.tools.Validator import economy

SLUT_SUCCESS_CHANCE = 0.65
SLUT_MIN_REWARD = 150
SLUT_MAX_REWARD = 400
SLUT_PENALTY_MIN = 100
SLUT_PENALTY_MAX = 300

SLUT_SUCCESS_MESSAGES = [
    "провели ночь с богатым клиентом и получили щедрое вознаграждение",
    "танцевали в клубе и получили хорошие чаевые от восторженных гостей",
    "провели соблазнительную фотосессию для журнала — весьма прибыльно",
    "сопровождали влиятельную особу на вечеринку и получили солидную оплату",
    "поработали эскортом на закрытом мероприятии и заработали кучу денег",
    "провели приватный массаж для богатого клиента — отличные чаевые",
]

SLUT_FAIL_MESSAGES = [
    "полиция нравов устроила рейд — вас оштрафовали на месте",
    "клиент оказался мошенником и сбежал, не заплатив",
    "вас ограбили в темном переулке после работы",
    "ваши фото попали не в те руки — пришлось платить за молчание",
]


class Slut(commands.Cog):
    """Команда для рискованного заработка с кулдауном."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = database
        self.economy = EconomyManager(self.db)

    @commands.hybrid_command(name="slut", description="💋 Рискованный способ заработка")
    @economy(CheckCooldown("slut"))
    async def slut(self, ctx: commands.Context) -> None:
        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)

        await self.economy.update_cooldown(user_id, guild_id, "slut")

        if random.random() <= SLUT_SUCCESS_CHANCE:
            reward = random.randint(SLUT_MIN_REWARD, SLUT_MAX_REWARD)
            success, message = await self.economy.add_money(
                user_id, guild_id, reward, share_spousal=True, event="slut"
            )

            if not success:
                await ctx.reply(embed=EconomyEmbed.error(message), ephemeral=True)
                return

            embed = EconomyEmbed.result(
                action="Рискованный заработок",
                user=ctx.author,
                text=(
                    f"вы {random.choice(SLUT_SUCCESS_MESSAGES)}. "
                    f"Вы получили **{reward:,}** {Emojis.MONEY}!"
                ),
            )
        else:
            penalty = random.randint(SLUT_PENALTY_MIN, SLUT_PENALTY_MAX)
            wallet_balance = await self.economy.get_wallet(user_id, guild_id)
            actual_penalty = min(wallet_balance, penalty)

            if actual_penalty > 0:
                await self.economy.remove_money(
                    user_id, guild_id, actual_penalty, event="slut_penalty"
                )

            embed = EconomyEmbed.result(
                action="Рискованный заработок",
                user=ctx.author,
                text=(
                    f"{random.choice(SLUT_FAIL_MESSAGES)}. "
                    f"Вы потеряли **{actual_penalty:,}** {Emojis.MONEY}."
                ),
            )

        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Slut(bot))
