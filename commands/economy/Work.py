import random

from discord.ext import commands

from Niludetsu import Emojis
from Niludetsu.database.supabase_database import database
from Niludetsu.economy.checks import CheckCooldown
from Niludetsu.economy.manager import EconomyManager
from Niludetsu.embeds.Economy import EconomyEmbed
from Niludetsu.tools.Validator import economy

WORK_MESSAGES = [
    ("спасателем котов", "спас кота с дерева и получил премию от благодарного хозяина"),
    ("офисным клерком", "сортировал бумаги в мэрии: скучно, зато платят"),
    ("бариста", "отработал смену и идеально нарисовал сердечко на латте"),
    ("парковщиком", "парковал дирижабли и ловко избежал аварии — начальство оценило"),
    ("курьером", "разносил кофе разработчикам и собрал приличные чаевые"),
    ("сантехником", "чистил канализацию — аромат сомнительный, но зарплата настоящая"),
    ("IT-специалистом", "устранял баги у коллег и получил бонус за скорость"),
    ("охранником", "дежурил ночным охранником и поймал нарушителя"),
    ("музыкантом", "выступал уличным музыкантом — публика щедро отблагодарила"),
    ("гидом", "проводил экскурсию по городу и заработал уважение туристов"),
    ("доставщиком", "развозил пиццу, успев в рекордные сроки"),
    ("декоратором", "украсил витрину магазина — продажи взлетели, и начислили премию"),
]


class Work(commands.Cog):
    """Команда честного труда с кулдауном."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = database
        self.economy = EconomyManager(self.db)

    @commands.hybrid_command(
        name="work", description="⛑️ Получить зарплату за честный труд"
    )
    @economy(CheckCooldown("work"))
    async def work(self, ctx: commands.Context) -> None:
        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)

        reward = random.randint(120, 260)
        success, message = await self.economy.add_money(
            user_id, guild_id, reward, share_spousal=True, event="work"
        )
        if not success:
            await ctx.reply(embed=EconomyEmbed.error(message), ephemeral=True)
            return

        await self.economy.update_cooldown(user_id, guild_id, "work")

        job, story = random.choice(WORK_MESSAGES)

        embed = EconomyEmbed.result(
            action="Награда за работу",
            user=ctx.author,
            text=(
                f"сегодня вы работали как **{job}** и {story}. "
                f"Вы получили **{reward:,}** {Emojis.MONEY}!"
            ),
        )
        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Work(bot))
