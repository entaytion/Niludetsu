import random
from discord.ext import commands
from Niludetsu import EconomyManager, EconomyEmbed, Emojis
from Niludetsu.locale import _

WORK_MESSAGES = [
    ("спасателем котов", "спас кота с дерева и получил премию"),
    ("бариста", "отработал смену и идеально нарисовал сердечко на латте"),
    ("IT-специалистом", "устранил баги и получил бонус за скорость"),
    ("охранником", "дежурил ночью и поймал нарушителя"),
]

class Work(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.economy = EconomyManager()

    @commands.hybrid_command(name="work", description="Получить зарплату за честный труд")
    async def work(self, ctx):
        uid, gid = str(ctx.author.id), str(ctx.guild.id)
        t = _(ctx=ctx)
        
        cd = await self.economy.check_cooldown(uid, gid, "work")
        if cd.status == "cooldown":
            return await ctx.reply(embed=EconomyEmbed.error(t("economy", "work_cooldown", time=cd.message)), ephemeral=True)

        reward = random.randint(120, 260)
        res = await self.economy.add_money(uid, gid, reward, event="work")
        if not res:
            return await ctx.reply(embed=EconomyEmbed.error(res.message), ephemeral=True)

        await self.economy.update_cooldown(uid, gid, "work")
        job, story = random.choice(WORK_MESSAGES)
        embed = EconomyEmbed.result(
            action=t("economy", "work_title"),
            user=ctx.author,
            text=t("economy", "work_success", job=job, story=story, amount=f"{reward:,}", currency=Emojis.MONEY),
        )
        await ctx.reply(embed=embed, mention_author=False)

async def setup(bot):
    await bot.add_cog(Work(bot))
