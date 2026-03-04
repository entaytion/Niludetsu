import asyncio, discord, random, uuid
from dataclasses import dataclass, field
from discord import app_commands
from discord.ext import commands
from Niludetsu import Emojis, Colors, Embed
from Niludetsu.database.supabase_database import database
from Niludetsu.economy.manager import EconomyManager
from Niludetsu.economy.validators import EconomyValidator
from typing import Dict, List, Optional, Tuple

GAME_NAME = "Блекджек"

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
            raise ValueError("Колода опустела, продолжение игры невозможно.")
        return self.deck.pop()

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
                embed=Embed.error("Эта игра принадлежит другому игроку."), ephemeral=True
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
    """🎰 Блекджек с экономикой и поддержкой независимых сессий."""

    CARD_VALUES: Dict[str, int] = {
        "A": 11,
        "2": 2,
        "3": 3,
        "4": 4,
        "5": 5,
        "6": 6,
        "7": 7,
        "8": 8,
        "9": 9,
        "10": 10,
        "J": 10,
        "Q": 10,
        "K": 10,
    }

    CARD_EMOJIS: Dict[str, Dict[str, str]] = {
        "S": {
            "2": Emojis.TWO_SPADES,
            "3": Emojis.THREE_SPADES,
            "4": Emojis.FOUR_SPADES,
            "5": Emojis.FIVE_SPADES,
            "6": Emojis.SIX_SPADES,
            "7": Emojis.SEVEN_SPADES,
            "8": Emojis.EIGHT_SPADES,
            "9": Emojis.NINE_SPADES,
            "10": Emojis.TEN_SPADES,
            "J": Emojis.JACK_SPADES,
            "Q": Emojis.QUEEN_SPADES,
            "K": Emojis.KING_SPADES,
            "A": Emojis.ACE_SPADES,
        },
        "H": {
            "2": Emojis.TWO_FAVORITES,
            "3": Emojis.THREE_FAVORITES,
            "4": Emojis.FOUR_FAVORITES,
            "5": Emojis.FIVE_FAVORITES,
            "6": Emojis.SIX_FAVORITES,
            "7": Emojis.SEVEN_FAVORITES,
            "8": Emojis.EIGHT_FAVORITES,
            "9": Emojis.NINE_FAVORITES,
            "10": Emojis.TEN_FAVORITES,
            "J": Emojis.JACK_FAVORITES,
            "Q": Emojis.QUEEN_FAVORITES,
            "K": Emojis.KING_FAVORITES,
            "A": Emojis.ACE_FAVORITES,
        },
        "D": {
            "2": Emojis.TWO_DIAMONDS,
            "3": Emojis.THREE_DIAMONDS,
            "4": Emojis.FOUR_DIAMONDS,
            "5": Emojis.FIVE_DIAMONDS,
            "6": Emojis.SIX_DIAMONDS,
            "7": Emojis.SEVEN_DIAMONDS,
            "8": Emojis.EIGHT_DIAMONDS,
            "9": Emojis.NINE_DIAMONDS,
            "10": Emojis.TEN_DIAMONDS,
            "J": Emojis.JACK_DIAMONDS,
            "Q": Emojis.QUEEN_DIAMONDS,
            "K": Emojis.KING_DIAMONDS,
            "A": Emojis.ACE_DIAMONDS,
        },
        "C": {
            "2": Emojis.TWO_CLUBS,
            "3": Emojis.THREE_CLUBS,
            "4": Emojis.FOUR_CLUBS,
            "5": Emojis.FIVE_CLUBS,
            "6": Emojis.SIX_CLUBS,
            "7": Emojis.SEVEN_CLUBS,
            "8": Emojis.EIGHT_CLUBS,
            "9": Emojis.NINE_CLUBS,
            "10": Emojis.TEN_CLUBS,
            "J": Emojis.JACK_CLUBS,
            "Q": Emojis.QUEEN_CLUBS,
            "K": Emojis.KING_CLUBS,
            "A": Emojis.ACE_CLUBS,
        },
    }

    SUITS: Tuple[str, ...] = ("S", "H", "D", "C")

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = database
        self.economy = EconomyManager(self.db)
        self.validator = EconomyValidator(self.economy)

        self._games: Dict[str, BlackjackGameState] = {}
        self._lock = asyncio.Lock()

    # Хранилище состояний
    async def _store_game(self, game: BlackjackGameState) -> None:
        async with self._lock:
            self._games[game.game_id] = game

    async def fetch_game(self, game_id: str) -> Optional[BlackjackGameState]:
        async with self._lock:
            return self._games.get(game_id)

    async def _remove_game(self, game_id: str) -> Optional[BlackjackGameState]:
        async with self._lock:
            return self._games.pop(game_id, None)

    # Колода и расчёт
    def _build_deck(self) -> List[str]:
        deck = [f"{value}{suit}" for suit in self.SUITS for value in self.CARD_VALUES]
        random.shuffle(deck)
        return deck

    def _calculate_hand(self, hand: List[str]) -> int:
        total = 0
        aces = 0
        for card in hand:
            rank = card[:-1]
            if rank == "A":
                aces += 1
            else:
                total += self.CARD_VALUES[rank]
        for _ in range(aces):
            total += 11 if total + 11 <= 21 else 1
        return total

    def _format_cards(self, cards: List[str]) -> str:
        chunks: List[str] = []
        for card in cards:
            if card == "?":
                chunks.append("❓")
                continue
            suit = card[-1]
            rank = card[:-1]
            suit_map = self.CARD_EMOJIS.get(suit)
            if not suit_map:
                chunks.append("❔")
                continue
            chunks.append(suit_map.get(rank, "❔"))
        return "".join(chunks)

    def _format_state_embed(
        self,
        game: BlackjackGameState,
        *,
        hide_dealer: bool,
        avatar_url: Optional[str],
    ) -> Embed:
        player_total = self._calculate_hand(game.player_hand)
        dealer_cards = [game.dealer_hand[0], "?"] if hide_dealer else game.dealer_hand
        dealer_total = "?" if hide_dealer else self._calculate_hand(game.dealer_hand)

        embed = Embed(
            title="🎰 Блекджек",
            description=f"**Ставка:** {game.bet:,} {Emojis.MONEY}",
            color=Colors.PRIMARY,
        )
        embed.add_field(
            name=f"Ваши карты ({player_total})",
            value=self._format_cards(game.player_hand),
            inline=True,
        )
        embed.add_field(
            name=f"Карты дилера ({dealer_total})",
            value=self._format_cards(dealer_cards),
            inline=True,
        )
        if avatar_url:
            embed.set_thumbnail(url=avatar_url)
        return embed

    async def _attach_balance_footer(self, embed: Embed, user_id: str, guild_id: str) -> Embed:
        wallet = await self.economy.get_wallet(user_id, guild_id)
        bank = await self.economy.get_bank(user_id, guild_id)
        embed.set_footer(text=f"Кошелёк: {wallet:,} монет • Банк: {bank:,} монет")
        return embed

    # Игровой процесс
    async def _start_game(self, user_id: str, guild_id: str, bet: int) -> BlackjackGameState:
        deck = self._build_deck()
        player_hand = [deck.pop(), deck.pop()]
        dealer_hand = [deck.pop(), deck.pop()]
        natural = self._calculate_hand(player_hand) == 21

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
        total = self._calculate_hand(game.player_hand)

        if total > 21:
            embed = await self.finish_game(game, reason="bust")
            return embed, True

        avatar_url = await self._resolve_avatar(game.user_id)
        embed = self._format_state_embed(game, hide_dealer=True, avatar_url=avatar_url)
        embed.description += "\n🎴 Выберите: взять карту или остановиться."
        return embed, False

    async def finish_game(self, game: BlackjackGameState, reason: str) -> Embed:
        await self._remove_game(game.game_id)
        await self.validator.release_game(GAME_NAME, game.user_id, game.guild_id)

        player_total = self._calculate_hand(game.player_hand)
        dealer_total = self._calculate_hand(game.dealer_hand)

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
                dealer_total = self._calculate_hand(game.dealer_hand)

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
            description = (
                f"🤝 <@{game.user_id}>, ставка **{game.bet:,}** {Emojis.MONEY} возвращена: {explanation}"
            )
        elif outcome:
            await self._apply_win(game.user_id, game.guild_id, game.bet, multiplier)
            net = int(round(game.bet * (multiplier - 1)))
            description = (
                f"🏆 <@{game.user_id}>, вы выиграли **{net:,}** {Emojis.MONEY}, потому что {explanation}"
            )
        else:
            await self._apply_loss(game.user_id, game.guild_id, game.bet)
            description = (
                f"💥 <@{game.user_id}>, вы проиграли **{game.bet:,}** {Emojis.MONEY}, потому что {explanation}"
            )

        embed = Embed(title="🎰 Блекджек", description=description, color=Colors.PRIMARY)
        embed.add_field(
            name=f"Ваши карты ({player_total})",
            value=self._format_cards(game.player_hand),
            inline=True,
        )
        embed.add_field(
            name=f"Карты дилера ({dealer_total})",
            value=self._format_cards(game.dealer_hand),
            inline=True,
        )

        avatar_url = await self._resolve_avatar(game.user_id)
        if avatar_url:
            embed.set_thumbnail(url=avatar_url)

        embed = await self._attach_balance_footer(embed, game.user_id, game.guild_id)
        return embed

    async def _apply_loss(self, user_id: str, guild_id: str, amount: int) -> None:
        _ = user_id, guild_id, amount  # ставка уже списана до начала игры

    async def _refund(self, user_id: str, guild_id: str, amount: int) -> None:
        await self.economy.add_money(user_id, guild_id, amount, share_spousal=False)

    async def _apply_win(self, user_id: str, guild_id: str, bet: int, multiplier: float) -> None:
        payout = int(round(bet * multiplier))
        await self.economy.add_money(user_id, guild_id, payout)

    async def _resolve_avatar(self, user_id: str) -> Optional[str]:
        user_id_int = int(user_id)
        for guild in self.bot.guilds:
            member = guild.get_member(user_id_int)
            if member:
                return member.display_avatar.url
        try:
            user = await self.bot.fetch_user(user_id_int)
            return user.display_avatar.url
        except discord.HTTPException:
            return None

    # Команда
    @commands.hybrid_command(name="blackjack", aliases=("bj",), description="🃏 Сыграть в блекджек.")
    @app_commands.describe(bet="🪙 Ставка в монетах")
    async def blackjack(self, ctx: commands.Context, bet: Optional[str] = None) -> None:
        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)

        valid, bet_value, error_embed = await self.validator.validate_bet(bet, user_id, guild_id)
        if not valid:
            await ctx.reply(embed=error_embed, ephemeral=True)
            return

        claimed, clash_embed = await self.validator.claim_game(GAME_NAME, user_id, guild_id)
        if not claimed:
            await ctx.reply(embed=clash_embed, ephemeral=True)
            return

        removal_ok, removal_message = await self.economy.remove_money(user_id, guild_id, bet_value)
        if not removal_ok:
            await self.validator.release_game(GAME_NAME, user_id, guild_id)
            await ctx.reply(embed=Embed.error(removal_message), ephemeral=True)
            return

        await ctx.defer(ephemeral=False)

        game = await self._start_game(user_id, guild_id, bet_value)
        avatar_url = ctx.author.display_avatar.url

        if game.natural_blackjack:
            embed = await self.finish_game(game, reason="blackjack")
            await ctx.reply(embed=embed, mention_author=False)
            return

        embed = self._format_state_embed(game, hide_dealer=True, avatar_url=avatar_url)
        embed.description += "\nВыбирай: взять карту или остановиться."
        view = BlackjackView(self, game.game_id, ctx.author.id)
        message = await ctx.reply(embed=embed, view=view, mention_author=False)
        view.message = message

    def cog_unload(self) -> None:
        self._games.clear()

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Blackjack(bot))

