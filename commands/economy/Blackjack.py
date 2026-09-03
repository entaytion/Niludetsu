import asyncio, discord, random
from discord.ext import commands
from Niludetsu import EconomyManager, EconomyEmbed, Embed
from Niludetsu.locale import _, DEFAULT_LOCALE

SUIT_EMOJIS = {"D": "♦️", "H": "♥️", "C": "♣️", "S": "♠️"}
CARD_VALS = {"A": 11, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10, "J": 10, "Q": 10, "K": 10}

def get_hand_val(hand):
    val, aces = 0, 0
    for c in hand:
        r = c[:-1]
        if r == "A": aces += 1
        else: val += CARD_VALS[r]
    for _ in range(aces): val += 11 if val + 11 <= 21 else 1
    return val

def fmt_hand(hand): return " ".join(f"{SUIT_EMOJIS[c[-1]]}{c[:-1]}" for c in hand)

class BlackjackView(discord.ui.View):
    def __init__(self, cog, gid, uid, bet):
        super().__init__(timeout=45.0)
        self.cog, self.gid, self.uid, self.bet = cog, gid, uid, bet
        self.deck = [f"{r}{s}" for s in "SHDC" for r in CARD_VALS]
        random.shuffle(self.deck)
        self.p_hand = [self.deck.pop(), self.deck.pop()]
        self.d_hand = [self.deck.pop(), self.deck.pop()]

    @discord.ui.button(label="Взять карту", style=discord.ButtonStyle.success)
    async def hit(self, i, b):
        if i.user.id != self.uid: return
        self.p_hand.append(self.deck.pop())
        if get_hand_val(self.p_hand) > 21: await self._end(i, "bust")
        else: await i.response.edit_message(embed=self._build_embed())

    @discord.ui.button(label="Хватит", style=discord.ButtonStyle.danger)
    async def stand(self, i, b):
        if i.user.id != self.uid: return
        await self._end(i, "stand")

    def _build_embed(self, final=False):
        pv, dv = get_hand_val(self.p_hand), get_hand_val(self.d_hand)
        embed = Embed.info(title=DEFAULT_LOCALE.get("economy", {}).get("bj_title", "Блекджек"))
        embed.add_field(name=f"{DEFAULT_LOCALE.get('economy', {}).get('bj_hand_player', 'Ваша рука ({score})').format(score=pv)}", value=fmt_hand(self.p_hand))
        embed.add_field(name=f"{DEFAULT_LOCALE.get('economy', {}).get('bj_hand_dealer', 'Рука дилера ({score})').format(score=dv if final else '?')}", value=fmt_hand(self.d_hand if final else [self.d_hand[0], '?']))
        return embed

    async def _end(self, i, reason):
        for c in self.children: c.disabled = True
        pv = get_hand_val(self.p_hand)
        if reason == "stand":
            while (dv := get_hand_val(self.d_hand)) < 17: self.d_hand.append(self.deck.pop())
            dv = get_hand_val(self.d_hand)
            if dv > 21 or pv > dv: win, msg = True, DEFAULT_LOCALE.get("economy", {}).get("bj_result_win", "Вы выиграли!")
            elif pv < dv: win, msg = False, DEFAULT_LOCALE.get("economy", {}).get("bj_result_lose", "Вы проиграли.")
            else: win, msg = "push", DEFAULT_LOCALE.get("economy", {}).get("bj_result_push", "Ничья.")
        else: win, msg = False, DEFAULT_LOCALE.get("economy", {}).get("bj_result_bust", "Перебор! Вы проиграли.")

        if win == True: await self.cog.economy.add_money(str(self.uid), str(self.gid), self.bet * 2, event="bj_win")
        elif win == "push": await self.cog.economy.add_money(str(self.uid), str(self.gid), self.bet, event="bj_push")
        
        embed = self._build_embed(True)
        embed.description = DEFAULT_LOCALE.get("economy", {}).get("bj_bet_display", "Ставка: **{bet}**\n**{result}**").format(bet=self.bet, result=msg)
        await i.response.edit_message(embed=embed, view=None)

class Blackjack(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.economy = EconomyManager()

    @commands.hybrid_command(name="blackjack", aliases=("bj",), description="Сыграть в блекджек")
    async def blackjack(self, ctx, bet: str):
        t = _(ctx=ctx)
        val = int(bet) if bet.isdigit() else 0
        if val <= 0: return await ctx.reply(t("economy", "invalid_bet"), ephemeral=True)
        uid, gid = str(ctx.author.id), str(ctx.guild.id)
        
        res = await self.economy.remove_money(uid, gid, val, event="bj_bet")
        if res.status == "insufficient_funds":
            return await ctx.reply(embed=EconomyEmbed.error(t("economy", "insufficient_funds")), ephemeral=True)
        elif res.status == "error":
            return await ctx.reply(res.message, ephemeral=True)
            
        v = BlackjackView(self, gid, ctx.author.id, val)
        await ctx.reply(embed=v._build_embed(), view=v)

async def setup(bot): await bot.add_cog(Blackjack(bot))
