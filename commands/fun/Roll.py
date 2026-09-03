import random
import re
import discord
from discord.ext import commands
from Niludetsu import Embed

DICE_PATTERN = re.compile(r"^(\d+)?d(\d+)(?:([+-])(\d+))?$", re.IGNORECASE)

class Roll(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="roll", aliases=["ролл", "кубик", "dice"], description="Бросить случайное число или кубики (напр: 100, 2d6, d20+3)")
    async def roll(self, ctx: commands.Context, dice: str = "100") -> None:
        dice_str = dice.strip().lower()

        if dice_str.isdigit():
            max_val = int(dice_str)
            if max_val < 1:
                await ctx.reply(embed=Embed.error("Число должно быть больше 0!"), ephemeral=True)
                return
            if max_val > 1_000_000:
                await ctx.reply(embed=Embed.error("Максимальное число — 1,000,000!"), ephemeral=True)
                return

            result = random.randint(1, max_val)
            embed = Embed.default(
                title="🎲 Бросок кубика",
                description=f"{ctx.author.mention} выбросил **{result}** *(диапазон: 1–{max_val})*",
            )
            await ctx.reply(embed=embed)
            return

        match = DICE_PATTERN.match(dice_str)
        if not match:
            await ctx.reply(
                embed=Embed.error(
                    "Неверный формат! Примеры:\n"
                    "• `!roll 100` — случайное число от 1 до 100\n"
                    "• `!roll d20` — один 20-гранный кубик\n"
                    "• `!roll 2d6+3` — два 6-гранных кубика плюс 3"
                ),
                ephemeral=True,
            )
            return

        count_str, sides_str, sign, mod_str = match.groups()
        count = int(count_str) if count_str else 1
        sides = int(sides_str)
        mod = int(mod_str) if mod_str else 0
        if sign == "-":
            mod = -mod

        if count < 1 or count > 50:
            await ctx.reply(embed=Embed.error("Количество кубиков должно быть от 1 до 50!"), ephemeral=True)
            return

        if sides < 2 or sides > 1000:
            await ctx.reply(embed=Embed.error("Количество граней должно быть от 2 до 1000!"), ephemeral=True)
            return

        rolls = [random.randint(1, sides) for _ in range(count)]
        total = sum(rolls) + mod

        rolls_display = ", ".join(map(str, rolls))
        if len(rolls_display) > 100:
            rolls_display = rolls_display[:97] + "..."

        mod_text = ""
        if mod > 0:
            mod_text = f" + {mod}"
        elif mod < 0:
            mod_text = f" - {abs(mod)}"

        crit_note = ""
        if sides == 20 and count == 1:
            if rolls[0] == 20:
                crit_note = "\n🔥 **Натуральная 20! Критический успех!**"
            elif rolls[0] == 1:
                crit_note = "\n💀 **Критический провал (1)!**"

        embed = Embed.default(
            title=f"🎲 Бросок {dice_str}",
            description=f"{ctx.author.mention} бросает **{count}d{sides}{mod_text}**:\n\n"
                        f"Выпало: `[{rolls_display}]`{mod_text}\n"
                        f"Итог: **{total}**{crit_note}",
        )
        await ctx.reply(embed=embed)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Roll(bot))

