import asyncio, discord, random, uuid
from dataclasses import dataclass, field
from discord import app_commands
from discord.ext import commands
from Niludetsu import Emojis, Embed
from Niludetsu.database.supabase_database import database
from Niludetsu.economy.manager import EconomyManager
from Niludetsu.economy.validators import EconomyValidator
from Niludetsu.economy.checks import ParseAmount, EnsureBalance, ClaimGame, DeductMoney
from Niludetsu.tools.Validator import economy
from Niludetsu.embeds.Economy import EconomyEmbed
from typing import Dict, List, Optional, Tuple

GAME_NAME = "Блекджек"

SUIT_EMOJIS: Dict[str, str] = {
    "D": "<:aeCardDiamonds:1479914897289642126>",
    "H": "<:aeCardHearts:1479915635650593039>",
    "C": "<:aeCardClubs:1479915961942413412>",
    "S": "<:aeCardSpades:1479916131933491311>",
}

SUITS: Tuple[str, ...] = ("S", "H", "D", "C")

CARD_VALUES: Dict[str, int] = {
    "A": 11, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6,
    "7": 7, "8": 8, "9": 9, "10": 10, "J": 10, "Q": 10, "K": 10,
}


@dataclass
class BlackjackGameState:
    game_id: str
    user_id: str
    guild_id: str
    bet: int
    deck: List[str] = field(default_factory=list)
    player_hand: List[str] = field(default_factory=list)
    dealer_hand: List[str] = field(default_factory=list)
    natural_blackjack: bool = False

    def draw_card(self) -> str:
        if not self.deck:
            raise ValueError("Колода опустела.")
        return self.deck.pop()


def _calculate_hand(hand: List[str]) -> int:
    total = 0
    aces = 0
    for card in hand:
        rank = card[:-1]
        if rank == "A":
            aces += 1
        else:
            total += CARD_VALUES[rank]
    for _ in range(aces):
        total += 11 if total + 11 <= 21 else 1
    return total


def _format_card(card: str) -> str:
    if card == "?":
        return "❓"
    suit = card[-1]
    rank = card[:-1]
    emoji = SUIT_EMOJIS.get(suit, "❔")
    return f"{emoji}{rank}"


def _format_cards(cards: List[str]) -> str:
    return " ".join(_format_card(c) for c in cards)


def _build_deck() -> List[str]:
    deck = [f"{rank}{suit}" for suit in SUITS for rank in CARD_VALUES]
    random.shuffle(deck)
    return deck


class BlackjackView(discord.ui.View):
    def __init__(self, cog: "Blackjack", game_id: str, owner_id: int, *, timeout: float = 45.0):
        super().__init__(timeout=timeout)
        self.cog = cog
        self.game_id = game_id
        self.owner_id = owner_id
        self.message: Optional[discord.Message] = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                embed=Embed.error("Эта игра принадлежит другому игроку."), ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self) -> None:
        if game := await self.cog.fetch_game(self.game_id):
            embed = await self.cog.finish_game(game, reason="timeout")
            await self._safe_edit(embed, view=None)
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True

    async def _safe_edit(self, embed: Embed, view: Optional[discord.ui.View]) -> None:
        if not self.message:
            return
        try:
            await self.message.edit(embed=embed, view=view)
        except discord.HTTPException:
            pass

    @discord.ui.button(label="Взять карту", style=discord.ButtonStyle.success, emoji="🎯")
    async def hit(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        game = await self.cog.fetch_game(self.game_id)
        if not game:
            await interaction.response.send_message(embed=Embed.error("Игра не найдена."), ephemeral=True)
            return

        await interaction.response.defer()
        embed, finished = await self.cog.handle_hit(game)
        if finished:
            await self._safe_edit(embed, view=None)
        else:
            await interaction.message.edit(embed=embed, view=self)

    @discord.ui.button(label="Хватит", style=discord.ButtonStyle.danger, emoji="⏹️")
    async def stand(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        game = await self.cog.fetch_game(self.game_id)
        if not game:
            await interaction.response.send_message(embed=Embed.error("Игра не найдена."), ephemeral=True)
            return

        await interaction.response.defer()
        embed = await self.cog.finish_game(game, reason="stand")
        await self._safe_edit(embed, view=None)


class Blackjack(commands.Cog):
    """🃏 Блекджек с экономикой и независимыми сессиями."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = database
        self.economy = EconomyManager(self.db)
        self.validator = EconomyValidator(self.economy)
        self._games: Dict[str, BlackjackGameState] = {}
        self._lock = asyncio.Lock()

    async def _store_game(self, game: BlackjackGameState) -> None:
        async with self._lock:
            self._games[game.game_id] = game

    async def fetch_game(self, game_id: str) -> Optional[BlackjackGameState]:
        async with self._lock:
            return self._games.get(game_id)

    async def _remove_game(self, game_id: str) -> Optional[BlackjackGameState]:
        async with self._lock:
            return self._games.pop(game_id, None)

    def _format_state_embed(
        self,
        game: BlackjackGameState,
        *,
        hide_dealer: bool,
        member: discord.Member | discord.User,
        message: Optional[str] = None,
    ) -> Embed:
        player_total = _calculate_hand(game.player_hand)
        dealer_cards = [game.dealer_hand[0], "?"] if hide_dealer else game.dealer_hand
        dealer_total = "?" if hide_dealer else _calculate_hand(game.dealer_hand)

        embed = EconomyEmbed.game_lobby(
            action="Блекджек",
            user=member,
            bet=game.bet,
            description=message,
        )
        embed.add_field(
            name=f"Ваша рука ({player_total})",
            value=_format_cards(game.player_hand),
            inline=True,
        )
        embed.add_field(
            name=f"Рука дилера ({dealer_total})",
            value=_format_cards(dealer_cards),
            inline=True,
        )
        return embed

    async def _resolve_member(self, user_id: str, guild_id: str):
        uid = int(user_id)
        guild = self.bot.get_guild(int(guild_id))
        if guild:
            member = guild.get_member(uid)
            if member:
                return member
        return await self.bot.fetch_user(uid)

    async def _start_game(self, user_id: str, guild_id: str, bet: int) -> BlackjackGameState:
        deck = _build_deck()
        player_hand = [deck.pop(), deck.pop()]
        dealer_hand = [deck.pop(), deck.pop()]
        natural = _calculate_hand(player_hand) == 21

        game = BlackjackGameState(
            game_id=str(uuid.uuid4()),
            user_id=user_id,
            guild_id=guild_id,
            bet=bet,
            deck=deck,
            player_hand=player_hand,
            dealer_hand=dealer_hand,
            natural_blackjack=natural,
        )
        await self._store_game(game)
        return game

    async def handle_hit(self, game: BlackjackGameState) -> Tuple[Embed, bool]:
        game.player_hand.append(game.draw_card())
        total = _calculate_hand(game.player_hand)

        if total > 21:
            embed = await self.finish_game(game, reason="bust")
            return embed, True

        member = await self._resolve_member(game.user_id, game.guild_id)
        embed = self._format_state_embed(
            game,
            hide_dealer=True,
            member=member,
            message="Выбирай: взять карту или остановиться.",
        )
        return embed, False

    async def finish_game(self, game: BlackjackGameState, reason: str) -> Embed:
        await self._remove_game(game.game_id)
        await self.validator.release_game(GAME_NAME, game.user_id, game.guild_id)

        player_total = _calculate_hand(game.player_hand)
        dealer_total = _calculate_hand(game.dealer_hand)

        if reason == "timeout":
            outcome = False
            multiplier = 0.0
            explanation = "время ожидания истекло. Ставка сгорает."
        elif reason == "blackjack":
            outcome = True
            multiplier = 2.5
            explanation = "натуральный блекджек! Выплата 3:2."
        elif reason == "bust":
            outcome = False
            multiplier = 0.0
            explanation = f"перебор ({player_total} очков)."
        else:
            while dealer_total < 17:
                game.dealer_hand.append(game.draw_card())
                dealer_total = _calculate_hand(game.dealer_hand)

            if dealer_total > 21:
                outcome, multiplier, explanation = True, 2.0, f"у дилера перебор ({dealer_total})."
            elif player_total > dealer_total:
                outcome, multiplier, explanation = True, 2.0, (
                    f"у вас {player_total} против {dealer_total} у дилера."
                )
            elif player_total < dealer_total:
                outcome, multiplier, explanation = False, 0.0, (
                    f"у дилера {dealer_total}, у вас {player_total}."
                )
            else:
                outcome, multiplier, explanation = "push", 1.0, (
                    f"ничья: у обоих по {player_total}."
                )

        if outcome == "push":
            await self._refund(game.user_id, game.guild_id, game.bet)
            text = f"ставка **{game.bet:,}** {Emojis.MONEY} возвращена: {explanation}"
        elif outcome:
            await self._apply_win(game.user_id, game.guild_id, game.bet, multiplier)
            net = int(round(game.bet * (multiplier - 1)))
            text = f"вы выиграли **{net:,}** {Emojis.MONEY}, потому что {explanation}"
        else:
            text = f"вы проиграли **{game.bet:,}** {Emojis.MONEY}, потому что {explanation}"

        wallet = await self.economy.get_wallet(game.user_id, game.guild_id)
        member = await self._resolve_member(game.user_id, game.guild_id)

        cards_text = (
            f"\n\n**Ваша рука:** {_format_cards(game.player_hand)} (сумма: **{player_total}**)"
            f"\n**Рука дилера:** {_format_cards(game.dealer_hand)} (сумма: **{dealer_total}**)"
        )

        embed = EconomyEmbed.result(
            action="Блекджек",
            user=member,
            text=f"{text}{cards_text}",
            balance=wallet,
        )
        return embed

    async def _refund(self, user_id: str, guild_id: str, amount: int) -> None:
        await self.economy.add_money(user_id, guild_id, amount, share_spousal=False)

    async def _apply_win(self, user_id: str, guild_id: str, bet: int, multiplier: float) -> None:
        payout = int(round(bet * multiplier))
        await self.economy.add_money(user_id, guild_id, payout, event="blackjack")

    @commands.hybrid_command(name="blackjack", aliases=("bj",), description="🃏 Сыграть в блекджек.")
    @app_commands.describe(bet="🪙 Ставка в монетах")
    @economy(ParseAmount("bet"), EnsureBalance(), ClaimGame(GAME_NAME), DeductMoney("blackjack"))
    async def blackjack(self, ctx: commands.Context, bet: Optional[str] = None) -> None:
        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)
        bet_value = ctx.eco["amount"]

        game = await self._start_game(user_id, guild_id, bet_value)
        if game.natural_blackjack:
            embed = await self.finish_game(game, reason="blackjack")
            await ctx.reply(embed=embed, mention_author=False)
            return

        embed = self._format_state_embed(
            game,
            hide_dealer=True,
            member=ctx.author,
            message="Выбирай: взять карту или остановиться.",
        )
        view = BlackjackView(self, game.game_id, ctx.author.id)
        message = await ctx.reply(embed=embed, view=view, mention_author=False)
        view.message = message

    def cog_unload(self) -> None:
        self._games.clear()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Blackjack(bot))
