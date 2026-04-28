import random
from discord.ext import commands
from Niludetsu import EconomyManager, EconomyEmbed, Emojis

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
        
        cd = await self.economy.check_cooldown(uid, gid, "slut")
        if cd.status == "cooldown":
            return await ctx.reply(embed=EconomyEmbed.error(f"Нужен отдых! Вернитесь через **{cd.message}**."), ephemeral=True)

        await self.economy.update_cooldown(uid, gid, "slut")

        if random.random() <= SLUT_CHANCE:
            reward = random.randint(150, 400)
            res = await self.economy.add_money(uid, gid, reward, event="slut")
            text = f"вы {random.choice(MESSAGES_OK)}. Получено **{reward:,}** {Emojis.MONEY}!"
        else:
            penalty = random.randint(100, 300)
            res = await self.economy.remove_money(uid, gid, penalty, event="slut_penalty")
            lost = penalty if res.status == "success" else 0
            text = f"{random.choice(MESSAGES_FAIL)}. Потеряно **{lost:,}** {Emojis.MONEY}."

        await ctx.reply(embed=EconomyEmbed.result(action="Рискованный заработок", user=ctx.author, text=text), mention_author=False)

async def setup(bot):
    await bot.add_cog(Slut(bot))
