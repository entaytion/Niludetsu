import asyncio, discord
from discord import app_commands
from discord.ext import commands
from Niludetsu import Embed, Colors, Emojis, safe_edit, EconomyManager
from Niludetsu.database import database
from Niludetsu.locale import _

from typing import Dict, Optional, Tuple

CHOICES = {
    "rock": {"name": "Камень", "emoji": "🪨", "beats": "scissors"},
    "scissors": {"name": "Ножницы", "emoji": "✂️", "beats": "paper"},
    "paper": {"name": "Бумага", "emoji": "📄", "beats": "rock"},
}

GAME_TIMEOUT = 60.0

class RPSPickView(discord.ui.View):
    def __init__(self, game, player_id, t):
        super().__init__(timeout=GAME_TIMEOUT)
        self.game, self.player_id, self.picked, self.t = game, player_id, False, t

    async def _pick(self, interaction, choice):
        if interaction.user.id != self.player_id: return
        if self.picked: return await interaction.response.send_message(embed=Embed.error(self.t("fun", "rps_already_picked")), ephemeral=True)
        self.picked = True
        for c in self.children: c.disabled = True
        await interaction.response.edit_message(embed=Embed(description=self.t("fun", "rps_waiting", choice=f"{CHOICES[choice]['emoji']} {CHOICES[choice]['name']}"), color=Colors.PRIMARY), view=self)
        await self.game.register_choice(self.player_id, choice)

    @discord.ui.button(label="Камень", emoji="🪨")
    async def rock(self, i, b): await self._pick(i, "rock")
    @discord.ui.button(label="Ножницы", emoji="✂️")
    async def scissors(self, i, b): await self._pick(i, "scissors")
    @discord.ui.button(label="Бумага", emoji="📄")
    async def paper(self, i, b): await self._pick(i, "paper")

class RPSChallengeView(discord.ui.View):
    def __init__(self, game, t):
        super().__init__(timeout=GAME_TIMEOUT)
        self.game, self.t = game, t

    async def interaction_check(self, i):
        if i.user.id == self.game.challenger_id:
            await i.response.send_message(embed=Embed.error(self.t("fun", "rps_self_challenge")), ephemeral=True)
            return False
        if i.user.id != self.game.target_id:
            await i.response.send_message(embed=Embed.error(self.t("fun", "rps_not_for_you")), ephemeral=True)
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
                return await i.response.edit_message(content=self.t("fun", "rps_insufficient_one"), view=self)

        for c in self.children: c.disabled = True
        await i.response.edit_message(view=self)
        await self.game.start_picks(i)

    @discord.ui.button(label="Отклонить", emoji="❌", style=discord.ButtonStyle.danger)
    async def decline(self, i, b):
        for c in self.children: c.disabled = True
        await i.response.edit_message(embed=Embed(description=self.t("fun", "rps_declined", user=f"<@{self.game.target_id}>"), color=Colors.ERROR), view=self)
        await self.game.cleanup()

class RPSGame:
    def __init__(self, cog, channel, challenger, target, bet, t):
        self.cog, self.channel, self.bet = cog, channel, bet
        self.challenger_id, self.target_id = challenger.id, target.id
        self.challenger_name, self.target_name = challenger.display_name, target.display_name
        self.guild_id = channel.guild.id
        self._choices, self._lock, self._resolved = {}, asyncio.Lock(), False
        self.t = t

    async def send_challenge(self, ctx):
        desc_parts = [self.t("fun", "rps_challenge_desc", challenger=f"**{self.challenger_name}**", target=f"**{self.target_name}**")]
        if self.bet:
            desc_parts.append(self.t("fun", "rps_bet_text", amount=f"**{self.bet:,}** {Emojis.MONEY}"))
        desc_parts.append(f"\n<@{self.target_id}>, принимаешь?")
        embed = Embed(title=self.t("fun", "rps_title"), description="\n".join(desc_parts), color=Colors.PRIMARY)
        self._challenge_message = await ctx.reply(embed=embed, view=RPSChallengeView(self, self.t), mention_author=False)

    async def start_picks(self, interaction):
        pick_embed = Embed(description=self.t("fun", "rps_pick_your_choice"), color=Colors.PRIMARY)
        for uid in (self.challenger_id, self.target_id):
            try:
                m = interaction.guild.get_member(uid)
                if m: await m.send(embed=pick_embed, view=RPSPickView(self, uid, self.t))
            except: pass
        if hasattr(self, '_challenge_message') and self._challenge_message:
            await self._challenge_message.edit(embed=Embed(title=self.t("fun", "rps_title"), description=self.t("fun", "rps_both_picking", challenger=f"**{self.challenger_name}**", target=f"**{self.target_name}**"), color=Colors.PRIMARY))

    async def register_choice(self, player_id, choice):
        async with self._lock:
            self._choices[player_id] = choice
            if len(self._choices) == 2: await self._resolve()

    async def _resolve(self):
        if self._resolved: return
        self._resolved = True
        c1, c2 = self._choices[self.challenger_id], self._choices[self.target_id]
        is_tie = (c1 == c2)
        
        if is_tie: res, win_id = self.t("fun", "rps_tie"), None
        elif CHOICES[c1]["beats"] == c2: res, win_id = self.t("fun", "rps_winner", name=f"**{self.challenger_name}**"), self.challenger_id
        else: res, win_id = self.t("fun", "rps_winner", name=f"**{self.target_name}**"), self.target_id

        desc = [f"{self.challenger_name}: {CHOICES[c1]['emoji']} **{CHOICES[c1]['name']}**", f"{self.target_name}: {CHOICES[c2]['emoji']} **{CHOICES[c2]['name']}**", "", res]
        if self.bet > 0:
            if win_id:
                payout = self.bet * 2
                await self.cog.economy.add_money(str(win_id), str(self.guild_id), payout, event="rps_win")
                desc.append(f"\n{self.t('fun', 'rps_prize', amount=f'**{payout:,}** {Emojis.MONEY}')}")
            elif is_tie:
                await self.cog.economy.add_money(str(self.challenger_id), str(self.guild_id), self.bet, event="rps_refund", share_spousal=False)
                await self.cog.economy.add_money(str(self.target_id), str(self.guild_id), self.bet, event="rps_refund", share_spousal=False)
                desc.append(f"\n{self.t('fun', 'rps_refund')}")

        if hasattr(self, '_challenge_message') and self._challenge_message:
            await safe_edit(self._challenge_message, embed=Embed(title=self.t("fun", "rps_result_title"), description="\n".join(desc), color=Colors.SUCCESS if win_id else Colors.PRIMARY), view=None)
        await self.cleanup()

    async def cleanup(self): self.cog._active_games.pop((min(self.challenger_id, self.target_id), max(self.challenger_id, self.target_id), self.guild_id), None)

class RPS(commands.Cog):
    def __init__(self, bot):
        self.bot, self.db = bot, database
        self.economy = EconomyManager(self.db)
        self._active_games = {}

    @commands.hybrid_command(name="rps", aliases=("кнб",), description="Камень-Ножницы-Бумага")
    async def rps(self, ctx, user: discord.Member, bet: Optional[str] = None):
        t = _(ctx=ctx)

        if user.id == ctx.author.id: return await ctx.reply(embed=Embed.error(t("fun", "rps_self_error")), ephemeral=True)
        if user.bot: return await ctx.reply(embed=Embed.error(t("fun", "rps_bot_error")), ephemeral=True)
        
        game_key = (min(ctx.author.id, user.id), max(ctx.author.id, user.id), ctx.guild.id)
        if game_key in self._active_games: return await ctx.reply(embed=Embed.error(t("fun", "rps_already_playing")), ephemeral=True)

        bet_val = int(bet) if bet and bet.isdigit() and int(bet) > 0 else 0
        if bet_val > 0:
            for p in (ctx.author, user):
                if await self.economy.get_wallet(str(p.id), str(ctx.guild.id)) < bet_val:
                    return await ctx.reply(embed=Embed.error(t("fun", "rps_insufficient_funds", name=f"**{p.display_name}**")), ephemeral=True)

        game = RPSGame(self, ctx.channel, ctx.author, user, bet_val, t)
        self._active_games[game_key] = game
        await game.send_challenge(ctx)

async def setup(bot): await bot.add_cog(RPS(bot))
