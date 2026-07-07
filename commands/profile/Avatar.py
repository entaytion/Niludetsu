import aiohttp, discord
from discord import app_commands
from discord.ext import commands
from io import BytesIO
from Niludetsu import Embed
from Niludetsu.api.LGBT import LGBT
from Niludetsu.locale import _
from typing import Optional

class Avatar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="avatar",
        aliases=["аватар"],
        description="Показать аватар пользователя"
    )
    @app_commands.describe(
        user="👤 Пользователь, чей аватар показать",
        mode="🌈 Режим отображения (необязательно)"
    )
    @app_commands.choices(mode=[
        app_commands.Choice(name="Радужный 🌈", value="lgbt")
    ])
    async def avatar(self, ctx: commands.Context, user: Optional[discord.Member] = None, mode: Optional[str] = None):
        await ctx.defer()
        t = _(ctx=ctx)
        target = user or ctx.author
        animated = target.display_avatar.is_animated()
        fmt = "gif" if animated else "png"
        url = target.display_avatar.with_format(fmt).url

        # Скачиваем аватар
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.read()

        # Проверяем аргумент mode для радужного эффекта
        name_text = t("profile", "avatar_profile_of", target_name=target.name) if target != ctx.author else t("profile", "avatar_your_profile")
        if mode and mode.lower() in ("lgbt", "лгбт"):
            if animated:
                await ctx.send(embed=Embed.error(description=t("profile", "avatar_animated_error")), ephemeral=True)
                return
            data = LGBT(data)
            fmt = "png"
            file = discord.File(BytesIO(data), filename=f"avatar.{fmt}")
            embed = Embed.info(
                title=t("profile", "avatar_title", target_name=name_text)
            )
            embed.set_image(url=f"attachment://avatar.{fmt}")
            await ctx.send(embed=embed, file=file)
        else:
            file = discord.File(BytesIO(data), filename=f"avatar.{fmt}")
            embed = Embed.info(
                title=t("profile", "avatar_title", target_name=name_text)
            )
            embed.set_image(url=f"attachment://avatar.{fmt}")
            await ctx.send(embed=embed, file=file)

async def setup(bot):
    await bot.add_cog(Avatar(bot))
