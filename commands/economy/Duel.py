import asyncio, discord, random
from discord import app_commands
from discord.ext import commands
from Niludetsu import EconomyManager, EconomyEmbed, Emojis, Embed, Colors

WEAPONS = {
    "sword": {"name": "Меч", "emoji": "⚔️", "dmg": (15, 25), "accuracy": 0.8},
    "bow": {"name": "Лук", "emoji": "🏹", "dmg": (12, 20), "accuracy": 0.85},
    "axe": {"name": "Топор", "emoji": "🪓", "dmg": (18, 30), "accuracy": 0.7},
}

class DuelInviteView(discord.ui.View):
    def __init__(self, challenger, opponent, bet, economy):
        super().__init__(timeout=30.0)
        self.challenger, self.opponent, self.bet, self.economy = challenger, opponent, bet, economy
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
        if member.id == ctx.author.id: return await ctx.reply("С собой нельзя!", ephemeral=True)
        if member.bot: return await ctx.reply("С ботом нельзя!", ephemeral=True)
        
        val = int(bet) if bet.isdigit() else 0
        gid = str(ctx.guild.id)
        
        # Проверка балансов
        for p in (ctx.author, member):
            acc = await self.economy.get_account(str(p.id), gid)
            if acc["balance"] < val: return await ctx.reply(f"У **{p.display_name}** недостаточно средств!", ephemeral=True)

        view = DuelInviteView(ctx.author, member, val, self.economy)
        msg = await ctx.reply(f"{member.mention}, вас вызывает на дуэль {ctx.author.mention}! Ставка: **{val:,}** {Emojis.MONEY}", view=view)
        
        await view.wait()
        if view.accepted is None: return await msg.edit(content="⏳ Время вышло, дуэль отменена.", view=None)
        if view.accepted is False: return await msg.edit(content="🏳️ Оппонент отказался.", view=None)

        # Списание ставок атомарно
        if val > 0:
            res1 = await self.economy.remove_money(str(ctx.author.id), gid, val, event="duel_bet")
            res2 = await self.economy.remove_money(str(member.id), gid, val, event="duel_bet")
            
            if res1.status != "success" or res2.status != "success":
                # Возвращаем ставки, если кто-то успел потратить
                if res1.status == "success": 
                    await self.economy.add_money(str(ctx.author.id), gid, val, event="duel_refund", share_spousal=False)
                if res2.status == "success": 
                    await self.economy.add_money(str(member.id), gid, val, event="duel_refund", share_spousal=False)
                return await msg.edit(content="У одного из игроков недостаточно средств! Дуэль отменена.", view=None)

        await msg.edit(content="⚔️ **ДУЭЛЬ НАЧАЛАСЬ!**", view=None)
        
        hps = {ctx.author.id: 100, member.id: 100}
        players = [ctx.author, member]
        
        while all(hp > 0 for hp in hps.values()):
            attacker = players[0]
            defender = players[1]
            
            weapon = random.choice(list(WEAPONS.values()))
            if random.random() <= weapon["accuracy"]:
                dmg = random.randint(*weapon["dmg"])
                hps[defender.id] -= dmg
                res_text = f"💥 {attacker.mention} ударил {defender.mention} используя **{weapon['name']}** на **{dmg}** урона!"
            else:
                res_text = f"🛡️ {attacker.mention} промахнулся!"
            
            await ctx.send(res_text)
            players.reverse()
            await asyncio.sleep(2)

        winner = ctx.author if hps[member.id] <= 0 else member
        loser = member if winner == ctx.author else ctx.author
        
        payout = val * 2
        if payout > 0: await self.economy.add_money(str(winner.id), gid, payout, event="duel_win")
        
        embed = EconomyEmbed.result(action="Дуэль", user=winner, text=f"победил в дуэли против {loser.mention}!\nНаграда: **{payout:,}** {Emojis.MONEY}", color=Colors.SUCCESS)
        await ctx.send(embed=embed)

async def setup(bot): await bot.add_cog(Duel(bot))
