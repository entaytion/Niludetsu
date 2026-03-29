import random

from discord.ext import commands

from Niludetsu import Embed
from Niludetsu.api import EightBall


class Ball(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="8ball",
        aliases=["шар"],
        description="🎱 Магический шар ответит на ваш вопрос",
    )
    async def ball(self, ctx: commands.Context, *, question: str = None):
        if not question:
            prefix = ctx.prefix or "!"
            await ctx.reply(
                embed=Embed.error(
                    description=f"Пожалуйста, задайте свой вопрос после команды, например: `{prefix}8ball будет ли завтра солнце?`"
                )
            )
            return

        response = random.choice(EightBall.responses)
        embed = Embed.default()
        embed.set_author(
            name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url
        )
        embed.add_field(name="> Вопрос:", value=f"```\n{question}\n```", inline=False)
        embed.add_field(name="> 🎱 Ответ:", value=f"```\n{response}\n```", inline=False)

        await ctx.reply(embed=embed)


async def setup(bot):
    await bot.add_cog(Ball(bot))
