import asyncio, discord, random
from discord import app_commands
from discord.ext import commands
from Niludetsu import EconomyManager, EconomyEmbed, Emojis, Embed, Colors, resolve_member

class Slots(commands.Cog):
    SYMBOLS = ["🍎", "💎", "🍊", "🍇", "🍒", "🍋", "7️⃣", "🎰"]
    MULT = {"🍎": 1.5, "💎": 2.0, "🍊": 1.3, "🍇": 1.8, "🍒": 1.5, "🍋": 1.2, "7️⃣": 7.0, "🎰": 10.0}

    def __init__(self, bot):
        self.bot = bot
        self.economy = EconomyManager()

    @commands.hybrid_command(name="slots", description="Испытать удачу в слотах")
    @app_commands.describe(bet="Ставка")
    async def slots(self, ctx, bet: str):
        val = int(bet) if bet.isdigit() else 0
        if val <= 0: return await ctx.reply("Ставка должна быть больше 0", ephemeral=True)
        
        uid, gid = str(ctx.author.id), str(ctx.guild.id)
        
        res = await self.economy.remove_money(uid, gid, val, event="slots_bet")
        if res.status == "insufficient_funds":
            return await ctx.reply(embed=EconomyEmbed.error("Недостаточно средств"), ephemeral=True)
        elif res.status == "error":
            return await ctx.reply(res.message, ephemeral=True)

        msg = await ctx.reply(embed=Embed(description="**Крутим...**", color=Colors.PRIMARY))

        res = [random.choice(self.SYMBOLS) for _ in range(3)]
        await asyncio.sleep(2)

        unique = set(res)
        win_mult = 0
        if len(unique) == 1: win_mult = self.MULT[res[0]]
        elif len(unique) == 2:
            for s in unique:
                if res.count(s) == 2: win_mult = self.MULT[s] / 2

        display = f"| {' | '.join(res)} |"
        if win_mult > 0:
            payout = int(val * win_mult)
            await self.economy.add_money(uid, gid, payout, event="slots_win")
            text = f"Результат: `{display}`\n🎉 Вы выиграли **{payout:,}** {Emojis.MONEY}!"
        else:
            text = f"Результат: `{display}`\n💥 Вы проиграли ставку."

        await msg.edit(embed=EconomyEmbed.result(action="Слоты", user=ctx.author, text=text, color=Colors.SUCCESS if win_mult > 0 else Colors.ERROR))

async def setup(bot): await bot.add_cog(Slots(bot))
