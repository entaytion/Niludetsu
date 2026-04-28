import asyncio, discord, random
from discord import app_commands
from discord.ext import commands
from Niludetsu import EconomyManager, EconomyEmbed, Emojis, Embed, Colors, safe_edit, safe_fetch_message, resolve_member

RED_NUMBERS = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
BLACK_NUMBERS = {2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35}

class RouletteBetView(discord.ui.View):
    def __init__(self, cog, owner_id, bet):
        super().__init__(timeout=45.0)
        self.cog, self.owner_id, self.bet = cog, owner_id, bet

    async def interaction_check(self, i):
        if i.user.id != self.owner_id:
            await i.response.send_message(embed=Embed.error("Это не ваша ставка!"), ephemeral=True)
            return False
        return True

    async def _pick(self, i, code):
        await i.response.defer()
        for c in self.children: c.disabled = True
        await i.edit_original_response(view=self)
        await self.cog.start_spin(i, self.owner_id, self.bet, code)

    @discord.ui.button(label="Красное", style=discord.ButtonStyle.danger, emoji="🟥")
    async def red(self, i, b): await self._pick(i, "red")
    @discord.ui.button(label="Чёрное", style=discord.ButtonStyle.secondary, emoji="⬛")
    async def black(self, i, b): await self._pick(i, "black")
    @discord.ui.button(label="Зелёное", style=discord.ButtonStyle.success, emoji="🟢")
    async def green(self, i, b): await self._pick(i, "green")
    @discord.ui.button(label="Чётное", style=discord.ButtonStyle.primary, emoji="2️⃣")
    async def even(self, i, b): await self._pick(i, "even")
    @discord.ui.button(label="Нечётное", style=discord.ButtonStyle.primary, emoji="1️⃣")
    async def odd(self, i, b): await self._pick(i, "odd")

class Roulette(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.economy = EconomyManager()

    @commands.hybrid_command(name="roulette", aliases=("casino", "рулетка"), description="Сыграть в рулетку")
    @app_commands.describe(bet="Сумма ставки")
    async def roulette(self, ctx, bet: str):
        val = int(bet) if bet.isdigit() else 0
        if val <= 0: return await ctx.reply("Ставка должна быть больше 0", ephemeral=True)
        
        acc = await self.economy.get_account(str(ctx.author.id), str(ctx.guild.id))
        if acc["balance"] < val: return await ctx.reply(embed=EconomyEmbed.error("Недостаточно средств"), ephemeral=True)

        embed = EconomyEmbed.game_lobby(action="🎰 Рулетка", user=ctx.author, bet=val, description="Выберите тип ставки кнопками ниже.")
        await ctx.reply(embed=embed, view=RouletteBetView(self, ctx.author.id, val))

    async def start_spin(self, interaction, uid, bet, code):
        res = await self.economy.remove_money(str(uid), str(interaction.guild_id), bet, event="roulette_bet")
        if res.status != "success":
            return await interaction.edit_original_response(embed=EconomyEmbed.error("Недостаточно средств для этой ставки!"), view=None)
        
        res_num = random.randint(0, 36)
        color = "red" if res_num in RED_NUMBERS else "black" if res_num in BLACK_NUMBERS else "green"
        
        # Простая анимация
        for _ in range(3):
            await interaction.edit_original_response(embed=Embed(description="**Крутим колесо...**", color=Colors.PRIMARY))
            await asyncio.sleep(1)

        win = False
        mult = 2.0
        if code == "red": win = res_num in RED_NUMBERS
        elif code == "black": win = res_num in BLACK_NUMBERS
        elif code == "green": win = res_num == 0; mult = 35.0
        elif code == "even": win = res_num != 0 and res_num % 2 == 0
        elif code == "odd": win = res_num % 2 == 1
        
        if win:
            payout = int(bet * mult)
            await self.economy.add_money(str(uid), str(interaction.guild_id), payout, event="roulette_win")
            text = f"🎉 Выпало **{res_num}** ({'🔴' if color=='red' else '⚫' if color=='black' else '🟢'}).\nВы выиграли **{payout:,}** {Emojis.MONEY}!"
        else:
            text = f"💥 Выпало **{res_num}** ({'🔴' if color=='red' else '⚫' if color=='black' else '🟢'}).\nВы проиграли свою ставку."

        await interaction.edit_original_response(embed=EconomyEmbed.result(action="Рулетка", user=interaction.user, text=text, color=Colors.SUCCESS if win else Colors.ERROR))

async def setup(bot): await bot.add_cog(Roulette(bot))
