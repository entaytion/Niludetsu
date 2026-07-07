import random

from discord.ext import commands

from Niludetsu import Embed
from Niludetsu.api import EightBall
from Niludetsu.locale import _


class Ball(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="8ball",
        aliases=["шар"],
        description="Магический шар ответит на ваш вопрос",
    )
    async def ball(self, ctx: commands.Context, *, question: str = None):
        t = _(ctx=ctx)

        if not question:
            prefix = ctx.prefix or "!"
            await ctx.reply(
                embed=Embed.error(
                    description=t("fun", "8ball_question", prefix=prefix)
                )
            )
            return

        response = random.choice(EightBall.responses)
        embed = Embed.default()
        embed.set_author(
            name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url
        )
        embed.add_field(name=t("fun", "8ball_field_question"), value=f"```\n{question}\n```", inline=False)
        embed.add_field(name=t("fun", "8ball_field_answer"), value=f"```\n{response}\n```", inline=False)

        await ctx.reply(embed=embed)


async def setup(bot):
    await bot.add_cog(Ball(bot))
