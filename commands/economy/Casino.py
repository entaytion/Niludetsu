import asyncio, discord, random
from dataclasses import dataclass
from discord import app_commands
from discord.ext import commands
from Niludetsu import Emojis, Embed, Colors, resolve_member, safe_edit, safe_fetch_message, GameView
from Niludetsu.embeds.Economy import EconomyEmbed
from Niludetsu.database.supabase_database import database
from Niludetsu.economy.manager import EconomyManager
from Niludetsu.economy.validators import EconomyValidator
from Niludetsu.economy.checks import ParseAmount, EnsureBalance, ClaimGame, DeductMoney
from Niludetsu.tools.Validator import economy
from typing import Dict, List, Optional, Tuple

GAME_NAME = "Рулетка"

RED_NUMBERS = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
BLACK_NUMBERS = {2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35}

BET_MAP = {
    "красное": "red",
    "черное": "black",
    "зеленое": "green",
    "четное": "even",
    "нечетное": "odd",
}

MULTIPLIERS = {
    "red": 2.0,
    "black": 2.0,
    "green": 35.0,
    "even": 2.0,
    "odd": 2.0,
}

COLOR_SYMBOLS = {
    "red": "🟥",
    "black": "⬛",
    "green": "🟢",
}

@dataclass
class RouletteState:
    user_id: str
    guild_id: str
    channel_id: int
    message_id: int
    bet_amount: int
    bet_code: Optional[str] = None

class RouletteBetView(GameView):
    def __init__(self, cog: "Roulette", message_id: int, owner_id: int, *, timeout: float = 45.0):
        super().__init__(timeout=timeout)
        self.cog = cog
        self.message_id = message_id
        self.owner_id = owner_id
        self.message: Optional[discord.Message] = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                embed=Embed.error("Эта ставка принадлежит другому игроку."),
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self) -> None:
        await self.disable_all()
        await self.cog.handle_timeout(self.message_id)

    async def make_choice(self, interaction: discord.Interaction, bet_code: str) -> None:
        await interaction.response.defer()
        await self.disable_all()
        await self.cog.resolve_bet(self.message_id, bet_code)

    @discord.ui.button(label="Красное", style=discord.ButtonStyle.danger, emoji="🟥")
    async def red(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.make_choice(interaction, "red")

    @discord.ui.button(label="Чёрное", style=discord.ButtonStyle.secondary, emoji="⬛")
    async def black(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.make_choice(interaction, "black")

    @discord.ui.button(label="Зелёное", style=discord.ButtonStyle.success, emoji="🟢")
    async def green(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.make_choice(interaction, "green")

    @discord.ui.button(label="Чётное", style=discord.ButtonStyle.primary, emoji="2️⃣")
    async def even(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.make_choice(interaction, "even")

    @discord.ui.button(label="Нечётное", style=discord.ButtonStyle.primary, emoji="1️⃣")
    async def odd(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.make_choice(interaction, "odd")

class Roulette(commands.Cog):
    """🎰 Рулетка: выбор ставки, плавная анимация вращения и опора на экономику."""

    WINDOW = 5
    FRAME_DELAYS = [0.22, 0.28, 0.36, 0.48, 0.65]

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = database
        self.economy = EconomyManager(self.db)
        self.validator = EconomyValidator(self.economy)
        self._games: Dict[int, RouletteState] = {}
        self._lock = asyncio.Lock()

    async def _store_game(self, message_id: int, state: RouletteState) -> None:
        async with self._lock:
            self._games[message_id] = state

    async def _pop_game(self, message_id: int) -> Optional[RouletteState]:
        async with self._lock:
            return self._games.pop(message_id, None)

    async def _get_game(self, message_id: int) -> Optional[RouletteState]:
        async with self._lock:
            return self._games.get(message_id)

    @commands.hybrid_command(
        name="roulette",
        aliases=("casino", "рулетка"),
        description="🎰 Рулетка — выбери ставку и проверь удачу.",
    )
    @app_commands.describe(bet="🪙 Сумма ставки")
    @economy(ParseAmount("bet"), EnsureBalance(), ClaimGame(GAME_NAME), DeductMoney("roulette"))
    async def roulette(self, ctx: commands.Context, bet: Optional[str] = None) -> None:
        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)
        bet_value = ctx.eco["amount"]

        embed = EconomyEmbed.game_lobby(
            action="🎰 Рулетка | Выбор ставки",
            user=ctx.author,
            bet=bet_value,
            description=(
                "Выберите тип ставки:\n"
                "🟥 Красное — ×2\n"
                "⬛ Чёрное — ×2\n"
                "🟢 Зелёное — ×35\n"
                "2️⃣ Чётное — ×2\n"
                "1️⃣ Нечётное — ×2"
            ),
        )

        message = await ctx.reply(embed=embed, mention_author=False)
        view = RouletteBetView(self, message.id, ctx.author.id)
        view.message = message
        await message.edit(view=view)

        state = RouletteState(
            user_id=user_id,
            guild_id=guild_id,
            channel_id=message.channel.id,
            message_id=message.id,
            bet_amount=bet_value,
        )
        await self._store_game(message.id, state)

    async def resolve_bet(self, message_id: int, bet_code: str) -> None:
        state = await self._get_game(message_id)
        if not state:
            return
        state.bet_code = bet_code
        await self.spin_wheel(state)

    async def spin_wheel(self, state: RouletteState) -> None:
        channel = self.bot.get_channel(state.channel_id)
        if not isinstance(channel, discord.TextChannel):
            await self._cleanup(state, refund=True)
            return

        message = await safe_fetch_message(channel, state.message_id)
        if not message:
            await self._cleanup(state, refund=True)
            return

        member = await resolve_member(self.bot, state.user_id, state.guild_id)
        result_number, frames = self._generate_frames()
        for delay, frame in frames[:-1]:
            await message.edit(embed=self._build_spin_embed(frame, member, state.bet_amount))
            await asyncio.sleep(delay)

        final_delay, final_frame = frames[-1]
        await message.edit(embed=self._build_spin_embed(final_frame, member, state.bet_amount))
        await asyncio.sleep(final_delay)

        won, multiplier = self._check_win(result_number, state.bet_code)
        payout = int(round(state.bet_amount * multiplier)) if won else 0
        if won:
            await self.economy.add_money(state.user_id, state.guild_id, payout, event="roulette")

        result_embed = await self._build_result_embed(state, final_frame, result_number, won, multiplier, payout)

        await message.edit(embed=result_embed, view=None)
        await self._cleanup(state, refund=False)

    async def handle_timeout(self, message_id: int) -> None:
        state = await self._pop_game(message_id)
        if not state:
            return

        await self.economy.add_money(state.user_id, state.guild_id, state.bet_amount)
        await self.validator.release_game(GAME_NAME, state.user_id, state.guild_id)

        channel = self.bot.get_channel(state.channel_id)
        if not isinstance(channel, discord.TextChannel):
            return

        message = await safe_fetch_message(channel, state.message_id)
        if not message:
            return

        member = await resolve_member(self.bot, state.user_id, state.guild_id)
        embed = EconomyEmbed.result(
            action="Рулетка",
            user=member,
            text=f"время выбора ставки вышло. Ставка возвращена.",
        )
        await safe_edit(message, embed=embed, view=None)

    async def _cleanup(self, state: RouletteState, refund: bool) -> None:
        await self._pop_game(state.message_id)
        await self.validator.release_game(GAME_NAME, state.user_id, state.guild_id)
        if refund:
            await self.economy.add_money(state.user_id, state.guild_id, state.bet_amount)

    def _generate_frames(self) -> Tuple[int, List[Tuple[float, List[int]]]]:
        window = self.WINDOW
        steps = len(self.FRAME_DELAYS)
        result = random.randint(0, 36)

        sequence = [random.randint(0, 36) for _ in range(window + steps - 1)] + [result]

        frames: List[Tuple[float, List[int]]] = []
        for index, delay in enumerate(self.FRAME_DELAYS):
            frame = sequence[index : index + window]
            frames.append((delay, frame))

        return result, frames

    def _format_frame(self, numbers: List[int]) -> str:
        return " | ".join(f"{COLOR_SYMBOLS[self._number_color(num)]}{num:02d}" for num in numbers)

    def _arrow_line(self, formatted_line: str) -> str:
        padding = max(0, len(formatted_line) // 2)
        return " " * padding + "↑"

    def _build_spin_embed(self, frame: List[int], member: discord.User, bet: int) -> Embed:
        formatted = self._format_frame(frame)
        description = (
            "```\n"
            f"{formatted}\n"
            f"{self._arrow_line(formatted)}\n"
            "```\n"
            "💫 Крутим..."
        )
        return EconomyEmbed.game_lobby(
            action="Рулетка",
            user=member,
            bet=bet,
            description=description,
        )

    async def _build_result_embed(
        self,
        state: RouletteState,
        frame: List[int],
        number: int,
        won: bool,
        multiplier: float,
        payout: int,
    ) -> discord.Embed:
        formatted = self._format_frame(frame)
        outcome_text = "🎉 Победа!" if won else "💥 Поражение."
        bet_name = self._bet_label(state.bet_code)
        diff = payout - state.bet_amount if won else -state.bet_amount

        member = await resolve_member(self.bot, state.user_id, state.guild_id)

        text = (
            "```\n\n"
            f"{formatted}\n"
            f"{self._arrow_line(formatted)}\n"
            "```\n"
            f"Выпало число **{number}** {COLOR_SYMBOLS[self._number_color(number)]}\n"
            f"{outcome_text} Вы поставили на **{bet_name}**.\n"
            f"Изменение баланса: {diff:+,} {Emojis.MONEY}"
        )

        return EconomyEmbed.result(
            action="Рулетка",
            user=member,
            text=text,
            color=Colors.SUCCESS if won else Colors.ERROR,
        )

    def _check_win(self, number: int, bet_code: Optional[str]) -> Tuple[bool, float]:
        if bet_code is None:
            return False, 0.0
        if bet_code == "red":
            won = number in RED_NUMBERS
        elif bet_code == "black":
            won = number in BLACK_NUMBERS
        elif bet_code == "green":
            won = number == 0
        elif bet_code == "even":
            won = number != 0 and number % 2 == 0
        elif bet_code == "odd":
            won = number != 0 and number % 2 == 1
        else:
            won = False
        return won, MULTIPLIERS.get(bet_code, 0.0)

    def _number_color(self, number: int) -> str:
        if number in RED_NUMBERS:
            return "red"
        if number in BLACK_NUMBERS:
            return "black"
        return "green"

    def _bet_label(self, bet_code: Optional[str]) -> str:
        for name, code in BET_MAP.items():
            if code == bet_code:
                return name
        return "?"


    def cog_unload(self) -> None:
        self._games.clear()

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Roulette(bot))
