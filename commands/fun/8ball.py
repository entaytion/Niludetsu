import discord, random
from discord import app_commands
from discord.ext import commands
from Niludetsu import Embed
from Niludetsu.api import EightBall

class Ball(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="8ball", description="🎱 Магический шар ответит на ваш вопрос")
    @app_commands.describe(question="🎱 Ваш вопрос к магическому шару")
    async def ball(self, ctx: commands.Context, *, question: str = None):
        if ctx.interaction is None and not question:
            prefix = ctx.prefix or ""
            invoked = ctx.invoked_with or "8ball"
            content = getattr(ctx.message, "content", "")
            question = content[len(prefix + invoked):].strip()

        if not question:
            if ctx.interaction:
                await ctx.send(
                    embed=Embed.error(
                        description="Пожалуйста, задайте свой вопрос после команды, например: `/8ball будет ли завтра солнце?`"
                    ),
                    ephemeral=True
                )
            else:
                await ctx.reply(
                    embed=Embed.error(
                        description="Пожалуйста, задайте свой вопрос после команды, например: `!8ball будет ли завтра солнце?`"
                    )
                )
            return

        response = random.choice(EightBall.responses)
        embed = Embed.default()
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        embed.add_field(
            name="> Вопрос:",
            value=f"```\n{question}\n```",
            inline=False
        )
        embed.add_field(
            name="> 🎱 Ответ:",
            value=f"```\n{response}\n```",
            inline=False
        )

        if ctx.interaction:
            await ctx.send(embed=embed)
        else:
            await ctx.reply(embed=embed)

async def setup(bot):
    await bot.add_cog(Ball(bot))

