import discord, time
from discord import app_commands
from discord.ext import commands
from Niludetsu import Embed, Colors
from Niludetsu.locale import _
from typing import Dict, Optional, Tuple


class AFK(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._afk: Dict[Tuple[int, int], Tuple[str, float]] = {}

    def _key(self, user_id: int, guild_id: int) -> Tuple[int, int]:
        return user_id, guild_id


    @commands.hybrid_command(
        name="afk",
        aliases=("афк",),
        description="Установить AFK-статус",
    )
    @app_commands.describe(reason="Причина AFK")
    async def afk(self, ctx: commands.Context, *, reason: Optional[str] = None) -> None:
        t = _(ctx=ctx)
        key = self._key(ctx.author.id, ctx.guild.id)
        reason = reason or t("utilities", "afk_reason_default")

        if key in self._afk:
            del self._afk[key]
            await ctx.reply(
                embed=Embed(
                    description=t("utilities", "afk_removed_desc", name=ctx.author.display_name),
                    color=Colors.SUCCESS,
                ),
                mention_author=False,
            )
            return

        self._afk[key] = (reason, time.time())
        await ctx.reply(
            embed=Embed(
                description=t("utilities", "afk_set_desc", name=ctx.author.display_name, reason=reason),
                color=Colors.PRIMARY,
            ),
            mention_author=False,
        )


    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or not message.guild:
            return

        t = _(guild_id=message.guild.id, bot=self.bot)
        guild_id = message.guild.id

        author_key = self._key(message.author.id, guild_id)
        if author_key in self._afk:
            prev_reason, went_afk_at = self._afk.pop(author_key)
            duration = self._format_duration(time.time() - went_afk_at)
            try:
                await message.reply(
                    embed=Embed(
                        description=t("utilities", "afk_removed_duration", name=message.author.display_name, duration=duration),
                        color=Colors.SUCCESS,
                    ),
                    mention_author=False,
                    delete_after=8,
                )
            except discord.HTTPException:
                pass

        if not message.mentions:
            return

        lines = []
        for mentioned in message.mentions:
            key = self._key(mentioned.id, guild_id)
            entry = self._afk.get(key)
            if entry:
                reason, went_afk_at = entry
                duration = self._format_duration(time.time() - went_afk_at)
                lines.append(
                    t("utilities", "afk_return_desc", name=mentioned.display_name, reason=reason, duration=duration)
                )

        if lines:
            try:
                await message.reply(
                    embed=Embed(
                        description="\n".join(lines),
                        color=Colors.PRIMARY,
                    ),
                    mention_author=False,
                    delete_after=12,
                )
            except discord.HTTPException:
                pass

    @staticmethod
    def _format_duration(seconds: float) -> str:
        s = int(seconds)
        if s < 60:
            return f"{s} сек"
        if s < 3600:
            m = s // 60
            return f"{m} мин"
        h = s // 3600
        m = (s % 3600) // 60
        if m:
            return f"{h} ч {m} мин"
        return f"{h} ч"


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AFK(bot))
