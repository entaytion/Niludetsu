import discord, io
from discord import app_commands
from discord.ext import commands
from Niludetsu import Embed
from Niludetsu.levels.image import LevelCardRenderer
from Niludetsu.levels.manager import LevelManager
from typing import Optional

class LevelCard(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.levels = LevelManager()
        self.renderer = LevelCardRenderer()

    @commands.hybrid_command(
        name="level",
        aliases=["ранг", "уровень"],
        description="📊 Показать уровень пользователя",
    )
    @app_commands.describe(user="👤 Чью карточку уровня показать (по умолчанию — вашу)")
    async def level_cmd(
        self,
        ctx: commands.Context,
        user: Optional[discord.Member] = None,
    ) -> None:
        """Рендерит и отправляет карточку уровня."""
        interaction = getattr(ctx, "interaction", None)

        if interaction and not interaction.response.is_done():
            await interaction.response.defer(thinking=True)

        async def respond(**kwargs):
            if interaction and interaction.response.is_done():
                await interaction.followup.send(**kwargs)
            else:
                if "mention_author" not in kwargs:
                    kwargs["mention_author"] = False
                await ctx.reply(**kwargs)

        if not ctx.guild:
            await respond(content="❌ Команду можно использовать только на сервере.")
            return

        target = user or ctx.author
        if target.bot:
            await respond(content="❌ Нельзя посмотреть уровень бота.")
            return

        profile = await self.levels.get_profile(str(ctx.guild.id), str(target.id))

        try:
            image_bytes = await self.renderer.render(target, profile)
        except FileNotFoundError as exc:
            await respond(
                embed=Embed.error(
                    title="Файл шаблона не найден",
                    description=str(exc),
                )
            )
            return
        except Exception as exc:
            await respond(
                embed=Embed.error(
                    title="Не удалось построить карточку",
                    description=f"Причина: {exc}",
                )
            )
            return

        file = discord.File(io.BytesIO(image_bytes), filename="level.png")
        await respond(file=file)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(LevelCard(bot))

