import random
from discord.ext import commands
from Niludetsu import Embed, Colors, Emojis
from Niludetsu.database.supabase_database import database
from Niludetsu.economy.manager import EconomyManager

WORK_MESSAGES = [
    "Ты спас кота с дерева и получил премию от благодарного хозяина.",
    "Ты сортировал бумаги в мэрии: скучно, зато платят.",
    "Ты отрабатывал смену бариста и идеально нарисовал сердечко на латте.",
    "Ты парковал дирижабли и ловко избежал аварии — начальство оценило.",
    "Ты разносил кофе разработчикам и собрал приличные чаевые.",
    "Ты чистил канализацию — аромат сомнительный, но зарплата настоящая.",
    "Ты устранял баги у коллег и получил бонус за скорость.",
    "Ты дежурил ночным охранником и поймал нарушителя.",
    "Ты выступал уличным музыкантом — публика щедро отблагодарила.",
    "Ты проводил экскурсию по городу и заработал уважение туристов.",
    "Ты развозил пиццу, успев в рекордные сроки.",
    "Ты украсил витрину магазина — продажи взлетели, и тебе начислили премию.",
]

class Work(commands.Cog):
    """Команда честного труда с кулдауном."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = database
        self.economy = EconomyManager(self.db)

    @commands.hybrid_command(name="work", description="⛑️ Получить зарплату за честный труд")
    async def work(self, ctx: commands.Context) -> None:
        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)

        can_use, error_msg = await self.economy.check_cooldown(user_id, guild_id, "work")

        if not can_use:
            await ctx.reply(
                embed=Embed.error(description=f"Ты уже трудился недавно! {error_msg}"),
                ephemeral=True,
            )
            return

        reward = random.randint(120, 260)
        success, message = await self.economy.add_money(
            user_id,
            guild_id,
            reward,
            share_spousal=True,
        )
        if not success:
            await ctx.reply(embed=Embed.error(description=message), ephemeral=True)
            return

        await self.economy.update_cooldown(user_id, guild_id, "work")

        wallet = await self.economy.get_wallet(user_id, guild_id)
        family = await self.economy.get_spousal_balance(user_id, guild_id)

        embed = Embed(
            title="🛠️ Смена завершена!",
            description=f"{random.choice(WORK_MESSAGES)}\n{message}",
            color=Colors.SUCCESS,
        )
        embed.add_field(name="Кошелёк", value=self.economy.format_money(wallet), inline=True)
        embed.add_field(name="Семейный счёт", value=self.economy.format_money(family), inline=True)
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        await ctx.reply(embed=embed, mention_author=False)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Work(bot))

