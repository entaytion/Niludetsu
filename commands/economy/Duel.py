import asyncio, discord, random
from discord.ext import commands
from Niludetsu.locale import _
from Niludetsu import EconomyManager, EconomyEmbed, Emojis, Colors

WEAPONS = {
    "sword": {"name": "Меч", "emoji": "⚔️", "dmg": (15, 25), "accuracy": 0.8},
    "bow": {"name": "Лук", "emoji": "🏹", "dmg": (12, 20), "accuracy": 0.85},
    "axe": {"name": "Топор", "emoji": "🪓", "dmg": (18, 30), "accuracy": 0.7},
}

class DuelInviteView(discord.ui.View):
    def __init__(self, challenger, opponent, bet, economy, t):
        super().__init__(timeout=30.0)
        self.challenger, self.opponent, self.bet, self.economy = challenger, opponent, bet, economy
        self.t = t
        self.accepted = None

    @discord.ui.button(label="Принять", style=discord.ButtonStyle.success, emoji="⚔️")
    async def accept(self, i, b):
        if i.user.id != self.opponent.id: return
        self.accepted = True
        self.stop()

    @discord.ui.button(label="Отказаться", style=discord.ButtonStyle.danger, emoji="🏳️")
    async def decline(self, i, b):
        if i.user.id != self.opponent.id: return
        self.accepted = False
        self.stop()

class Duel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.economy = EconomyManager()

    @commands.hybrid_command(name="duel", description="Вызвать игрока на дуэль")
    async def duel(self, ctx, member: discord.Member, bet: str = "0"):
        t = _(ctx=ctx)
        if member.id == ctx.author.id: return await ctx.reply(t("duel", "self_not_allowed"), ephemeral=True)
        if member.bot: return await ctx.reply(t("duel", "bot_not_allowed"), ephemeral=True)
        
        val = int(bet) if bet.isdigit() else 0
        gid = str(ctx.guild.id)
        
        for p in (ctx.author, member):
            acc = await self.economy.get_account(str(p.id), gid)
            if acc["balance"] < val: return await ctx.reply(t("duel", "insufficient", name=p.display_name), ephemeral=True)

        view = DuelInviteView(ctx.author, member, val, self.economy, t)
        msg = await ctx.reply(t("duel", "invite", opponent=member.mention, challenger=ctx.author.mention, bet=f"{val:,}", currency=Emojis.MONEY), view=view)
        
        await view.wait()
        if view.accepted is None: return await msg.edit(content=t("duel", "timeout"), view=None)
        if view.accepted is False: return await msg.edit(content=t("duel", "declined"), view=None)

        if val > 0:
            res1 = await self.economy.remove_money(str(ctx.author.id), gid, val, event="duel_bet")
            res2 = await self.economy.remove_money(str(member.id), gid, val, event="duel_bet")
            
            if res1.status != "success" or res2.status != "success":
                if res1.status == "success": 
                    await self.economy.add_money(str(ctx.author.id), gid, val, event="duel_refund", share_spousal=False)
                if res2.status == "success": 
                    await self.economy.add_money(str(member.id), gid, val, event="duel_refund", share_spousal=False)
                return await msg.edit(content=t("duel", "refund"), view=None)

        await msg.edit(content=t("duel", "started"), view=None)
        
        hps = {ctx.author.id: 100, member.id: 100}
        players = [ctx.author, member]
        
        while all(hp > 0 for hp in hps.values()):
            attacker = players[0]
            defender = players[1]
            
            weapon = random.choice(list(WEAPONS.values()))
            if random.random() <= weapon["accuracy"]:
                dmg = random.randint(*weapon["dmg"])
                hps[defender.id] -= dmg
                res_text = t("duel", "hit", attacker=attacker.mention, defender=defender.mention, weapon=weapon["name"], dmg=dmg)
            else:
                res_text = t("duel", "miss", attacker=attacker.mention)
            
            await ctx.send(res_text)
            players.reverse()
            await asyncio.sleep(2)

        winner = ctx.author if hps[member.id] <= 0 else member
        loser = member if winner == ctx.author else ctx.author
        
        payout = val * 2
        if payout > 0: await self.economy.add_money(str(winner.id), gid, payout, event="duel_win")
        
        embed = EconomyEmbed.result(action=t("duel", "title"), user=winner, text=t("duel", "victory", winner=winner.mention, loser=loser.mention, payout=f"{payout:,}", currency=Emojis.MONEY), color=Colors.SUCCESS)
        await ctx.send(embed=embed)

async def setup(bot): await bot.add_cog(Duel(bot))
