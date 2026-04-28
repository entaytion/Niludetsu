import asyncio, discord
from discord import app_commands
from discord.ext import commands
from Niludetsu import Embed, Colors, Emojis, safe_edit, EconomyManager
from Niludetsu.database import database

from typing import Dict, Optional, Tuple

CHOICES = {
    "rock": {"name": "Камень", "emoji": "🪨", "beats": "scissors"},
    "scissors": {"name": "Ножницы", "emoji": "✂️", "beats": "paper"},
    "paper": {"name": "Бумага", "emoji": "📄", "beats": "rock"},
}

GAME_TIMEOUT = 60.0

class RPSPickView(discord.ui.View):
    def __init__(self, game, player_id):
        super().__init__(timeout=GAME_TIMEOUT)
        self.game, self.player_id, self.picked = game, player_id, False

    async def _pick(self, interaction, choice):
        if interaction.user.id != self.player_id: return
        if self.picked: return await interaction.response.send_message(embed=Embed.error("Ты уже выбрал!"), ephemeral=True)
        self.picked = True
        for c in self.children: c.disabled = True
        await interaction.response.edit_message(embed=Embed(description=f"Ты выбрал **{CHOICES[choice]['emoji']} {CHOICES[choice]['name']}**. Ожидание соперника...", color=Colors.PRIMARY), view=self)
        await self.game.register_choice(self.player_id, choice)

    @discord.ui.button(label="Камень", emoji="🪨")
    async def rock(self, i, b): await self._pick(i, "rock")
    @discord.ui.button(label="Ножницы", emoji="✂️")
    async def scissors(self, i, b): await self._pick(i, "scissors")
    @discord.ui.button(label="Бумага", emoji="📄")
    async def paper(self, i, b): await self._pick(i, "paper")

class RPSChallengeView(discord.ui.View):
    def __init__(self, game):
        super().__init__(timeout=GAME_TIMEOUT)
        self.game = game

    async def interaction_check(self, i):
        if i.user.id == self.game.challenger_id:
            await i.response.send_message(embed=Embed.error("Нельзя принять свой же вызов!"), ephemeral=True)
            return False
        if i.user.id != self.game.target_id:
            await i.response.send_message(embed=Embed.error("Этот вызов не для тебя!"), ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Принять", emoji="✅", style=discord.ButtonStyle.success)
    async def accept(self, i, b):
        if self.game.bet > 0:
            res1 = await self.game.cog.economy.remove_money(str(self.game.challenger_id), str(self.game.guild_id), self.game.bet, event="rps_bet")
            res2 = await self.game.cog.economy.remove_money(str(self.game.target_id), str(self.game.guild_id), self.game.bet, event="rps_bet")
            if res1.status != "success" or res2.status != "success":
                if res1.status == "success": await self.game.cog.economy.add_money(str(self.game.challenger_id), str(self.game.guild_id), self.game.bet, event="rps_refund", share_spousal=False)
                if res2.status == "success": await self.game.cog.economy.add_money(str(self.game.target_id), str(self.game.guild_id), self.game.bet, event="rps_refund", share_spousal=False)
                for c in self.children: c.disabled = True
                return await i.response.edit_message(content="У одного из игроков недостаточно средств! Игра отменена.", view=self)

        for c in self.children: c.disabled = True
        await i.response.edit_message(view=self)
        await self.game.start_picks(i)

    @discord.ui.button(label="Отклонить", emoji="❌", style=discord.ButtonStyle.danger)
    async def decline(self, i, b):
        for c in self.children: c.disabled = True
        await i.response.edit_message(embed=Embed(description=f"<@{self.game.target_id}> отклонил вызов.", color=Colors.ERROR), view=self)
        await self.game.cleanup()

class RPSGame:
    def __init__(self, cog, channel, challenger, target, bet):
        self.cog, self.channel, self.bet = cog, channel, bet
        self.challenger_id, self.target_id = challenger.id, target.id
        self.challenger_name, self.target_name = challenger.display_name, target.display_name
        self.guild_id = channel.guild.id
        self._choices, self._lock, self._resolved = {}, asyncio.Lock(), False

    async def send_challenge(self, ctx):
        embed = Embed(title="Камень-Ножницы-Бумага", description=f"**{self.challenger_name}** вызывает **{self.target_name}** на дуэль!{f'\nСтавка: **{self.bet:,}** {Emojis.MONEY}' if self.bet else ''}\n\n<@{self.target_id}>, принимаешь?", color=Colors.PRIMARY)
        self._challenge_message = await ctx.reply(embed=embed, view=RPSChallengeView(self), mention_author=False)

    async def start_picks(self, interaction):
        pick_embed = Embed(description="Выбери свой ход:", color=Colors.PRIMARY)
        for uid in (self.challenger_id, self.target_id):
            try:
                m = interaction.guild.get_member(uid)
                if m: await m.send(embed=pick_embed, view=RPSPickView(self, uid))
            except: pass
        if hasattr(self, '_challenge_message') and self._challenge_message:
            await self._challenge_message.edit(embed=Embed(title="Камень-Ножницы-Бумага", description=f"**{self.challenger_name}** vs **{self.target_name}**\nОба игрока выбирают... ", color=Colors.PRIMARY))

    async def register_choice(self, player_id, choice):
        async with self._lock:
            self._choices[player_id] = choice
            if len(self._choices) == 2: await self._resolve()

    async def _resolve(self):
        if self._resolved: return
        self._resolved = True
        c1, c2 = self._choices[self.challenger_id], self._choices[self.target_id]
        is_tie = (c1 == c2)
        
        if is_tie: res, win_id = "🤝 **Ничья!**", None
        elif CHOICES[c1]["beats"] == c2: res, win_id = f"🎉 **{self.challenger_name}** побеждает!", self.challenger_id
        else: res, win_id = f"🎉 **{self.target_name}** побеждает!", self.target_id

        desc = [f"{self.challenger_name}: {CHOICES[c1]['emoji']} **{CHOICES[c1]['name']}**", f"{self.target_name}: {CHOICES[c2]['emoji']} **{CHOICES[c2]['name']}**", "", res]
        if self.bet > 0:
            if win_id:
                payout = self.bet * 2
                await self.cog.economy.add_money(str(win_id), str(self.guild_id), payout, event="rps_win")
                desc.append(f"\n💰 **{payout:,}** {Emojis.MONEY} забирает победитель!")
            elif is_tie:
                await self.cog.economy.add_money(str(self.challenger_id), str(self.guild_id), self.bet, event="rps_refund", share_spousal=False)
                await self.cog.economy.add_money(str(self.target_id), str(self.guild_id), self.bet, event="rps_refund", share_spousal=False)
                desc.append(f"\n💸 Ставки возвращены.")

        if hasattr(self, '_challenge_message') and self._challenge_message:
            await safe_edit(self._challenge_message, embed=Embed(title="Результат", description="\n".join(desc), color=Colors.SUCCESS if win_id else Colors.PRIMARY), view=None)
        await self.cleanup()

    async def cleanup(self): self.cog._active_games.pop((min(self.challenger_id, self.target_id), max(self.challenger_id, self.target_id), self.guild_id), None)

class RPS(commands.Cog):
    def __init__(self, bot):
        self.bot, self.db = bot, database
        self.economy = EconomyManager(self.db)
        self._active_games = {}

    @commands.hybrid_command(name="rps", aliases=("кнб",), description="Камень-Ножницы-Бумага")
    async def rps(self, ctx, user: discord.Member, bet: Optional[str] = None):
        if user.id == ctx.author.id: return await ctx.reply(embed=Embed.error("Нельзя играть с самим собой!"), ephemeral=True)
        if user.bot: return await ctx.reply(embed=Embed.error("Нельзя играть с ботом!"), ephemeral=True)
        
        game_key = (min(ctx.author.id, user.id), max(ctx.author.id, user.id), ctx.guild.id)
        if game_key in self._active_games: return await ctx.reply(embed=Embed.error("Между вами уже идёт игра!"), ephemeral=True)

        bet_val = int(bet) if bet and bet.isdigit() and int(bet) > 0 else 0
        if bet_val > 0:
            for p in (ctx.author, user):
                if await self.economy.get_wallet(str(p.id), str(ctx.guild.id)) < bet_val:
                    return await ctx.reply(embed=Embed.error(f"У **{p.display_name}** недостаточно средств!"), ephemeral=True)

        game = RPSGame(self, ctx.channel, ctx.author, user, bet_val)
        self._active_games[game_key] = game
        await game.send_challenge(ctx)

async def setup(bot): await bot.add_cog(RPS(bot))