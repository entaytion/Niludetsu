import datetime
import hashlib
import discord
from discord.ext import commands
from Niludetsu import Embed

class Ship(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @staticmethod
    def _calculate_compatibility(id1: int, id2: int) -> int:
        first, second = min(id1, id2), max(id1, id2)
        today = datetime.date.today().isoformat()
        seed_str = f"{first}:{second}:{today}"
        h = hashlib.sha256(seed_str.encode("utf-8")).hexdigest()
        val = int(h[:8], 16)
        return val % 101

    @staticmethod
    def _create_ship_name(name1: str, name2: str) -> str:
        half1 = name1[:max(2, len(name1) // 2)]
        half2 = name2[max(2, len(name2) // 2):]
        return (half1 + half2).capitalize()

    @staticmethod
    def _progress_bar(percent: int) -> str:
        filled = round(percent / 10)
        empty = 10 - filled
        return ("❤️" * filled) + ("🖤" * empty)

    @staticmethod
    def _verdict(percent: int) -> str:
        if percent < 15:
            return "Ледяной холод... Даже не пробуйте 🥶"
        elif percent < 35:
            return "Шансы сомнительные. Максимум дружба 🌧️"
        elif percent < 55:
            return "Обычные приятели. Может кофе попьёте? ☕"
        elif percent < 75:
            return "Искорка пробежала! Есть все шансы ✨"
        elif percent < 90:
            return "Очень горячо! Отличная пара 🔥"
        else:
            return "Идеальная пара! Чистая судьба, пора играть свадьбу 💍"

    @commands.hybrid_command(name="ship", description="Проверить совместимость двух участников")
    async def ship(
        self,
        ctx: commands.Context,
        target: discord.Member,
        second_target: discord.Member | None = None,
    ) -> None:
        user1 = ctx.author if second_target is None else target
        user2 = target if second_target is None else second_target

        if user1.id == user2.id:
            await ctx.reply(embed=Embed.error("Любовь к себе — это прекрасно, но шипперить себя с собой не выйдет!"), ephemeral=True)
            return

        percent = self._calculate_compatibility(user1.id, user2.id)
        bar = self._progress_bar(percent)
        ship_name = self._create_ship_name(user1.display_name, user2.display_name)
        verdict = self._verdict(percent)

        embed = Embed.default(
            title=f"💘 Шипперинг: {user1.display_name} + {user2.display_name}",
            description=f"Имя пары: **{ship_name}**\n\n"
                        f"Совместимость: **{percent}%**\n"
                        f"{bar}\n\n"
                        f"**Вердикт:** {verdict}",
        )
        if percent >= 75:
            embed.color = discord.Color.from_rgb(255, 105, 180)
        elif percent < 35:
            embed.color = discord.Color.from_rgb(100, 100, 120)

        embed.set_footer(text="Совместимость обновляется каждый день")
        await ctx.reply(embed=embed)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Ship(bot))

