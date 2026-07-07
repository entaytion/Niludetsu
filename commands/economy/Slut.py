import random
from discord.ext import commands
from Niludetsu import EconomyManager, EconomyEmbed, Emojis
from Niludetsu.locale import _

SLUT_CHANCE = 0.65

MESSAGES_OK = ["провели ночь с богатым клиентом", "танцевали в клубе и получили чаевые"]
MESSAGES_FAIL = ["полиция нравов устроила рейд", "вас ограбили в темном переулке"]

class Slut(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.economy = EconomyManager()

    @commands.hybrid_command(name="slut", description="Рискованный способ заработка")
    async def slut(self, ctx):
        uid, gid = str(ctx.author.id), str(ctx.guild.id)
        t = _(ctx=ctx)
        
        cd = await self.economy.check_cooldown(uid, gid, "slut")
        if cd.status == "cooldown":
            return await ctx.reply(embed=EconomyEmbed.error(t("economy", "slut_cooldown_text", time=cd.message)), ephemeral=True)

        await self.economy.update_cooldown(uid, gid, "slut")

        if random.random() <= SLUT_CHANCE:
            reward = random.randint(150, 400)
            res = await self.economy.add_money(uid, gid, reward, event="slut")
            text = t("economy", "slut_success_text", story=random.choice(MESSAGES_OK), amount=f"{reward:,}", currency=Emojis.MONEY)
        else:
            penalty = random.randint(100, 300)
            res = await self.economy.remove_money(uid, gid, penalty, event="slut_penalty")
            lost = penalty if res.status == "success" else 0
            text = t("economy", "slut_fail_text", story=random.choice(MESSAGES_FAIL), amount=f"{lost:,}", currency=Emojis.MONEY)

        await ctx.reply(embed=EconomyEmbed.result(action=t("economy", "slut_title"), user=ctx.author, text=text), mention_author=False)

async def setup(bot):
    await bot.add_cog(Slut(bot))
