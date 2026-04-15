import asyncio, discord, random
from dataclasses import dataclass
from discord import app_commands
from discord.ext import commands
from Niludetsu import Emojis, Embed, resolve_member, safe_edit, safe_fetch_message, GameView
from Niludetsu.embeds.Economy import EconomyEmbed
from Niludetsu.database.supabase_database import database
from Niludetsu.economy.manager import EconomyManager
from Niludetsu.economy.validators import EconomyValidator
from Niludetsu.economy.checks import ParseAmount, EnsureBalance, ClaimGame, DeductMoney
from Niludetsu.tools.Validator import economy
from typing import Dict, Optional

GAME_NAME = "Монетка"

@dataclass
class CoinflipState:
    user_id: str
    guild_id: str
    channel_id: int
    bet: int
    message_id: int
    choice: Optional[str] = None

class CoinflipView(GameView):
    def __init__(self, cog: "Coinflip", game_id: int, owner_id: int, *, timeout: float = 30.0):
        super().__init__(timeout=timeout)
        self.cog = cog
        self.game_id = game_id
        self.owner_id = owner_id
        self.message: Optional[discord.Message] = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                embed=Embed.error("Эта игра принадлежит другому игроку."),
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self) -> None:
        await self.disable_all()
        await self.cog.handle_timeout(self.game_id)

    @discord.ui.button(label="Орёл", style=discord.ButtonStyle.secondary, emoji="🦅")
    async def heads(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.process_choice(interaction, "heads")

    @discord.ui.button(label="Решка", style=discord.ButtonStyle.secondary, emoji="⚪")
    async def tails(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.process_choice(interaction, "tails")

    async def process_choice(self, interaction: discord.Interaction, choice: str) -> None:
        await interaction.response.defer()
        await self.disable_all()
        embed = await self.cog.resolve_game(self.game_id, choice)
        if embed:
            await safe_edit(self.message, embed=embed, view=None)

class Coinflip(commands.Cog):
    """🪙 Монетка: ставка х2 с учётом экономики и блокировкой мультисессий."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = database
        self.economy = EconomyManager(self.db)
        self.validator = EconomyValidator(self.economy)

        self._games: Dict[int, CoinflipState] = {}
        self._lock = asyncio.Lock()

    async def _store_game(self, message_id: int, state: CoinflipState) -> None:
        async with self._lock:
            self._games[message_id] = state

    async def _pop_game(self, message_id: int) -> Optional[CoinflipState]:
        async with self._lock:
            return self._games.pop(message_id, None)

    @commands.hybrid_command(
        name="coinflip",
        aliases=("монетка",),
        description="🪙 Сыграть в монетку и удвоить ставку.",
    )
    @app_commands.describe(bet="🪙 Сумма ставки")
    @economy(ParseAmount("bet"), EnsureBalance(), ClaimGame(GAME_NAME), DeductMoney("coinflip"))
    async def coinflip(self, ctx: commands.Context, bet: Optional[str] = None) -> None:
        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)
        bet_value = ctx.eco["amount"]

        embed = EconomyEmbed.game_lobby(
            action="🪙 Игра в монетку",
            user=ctx.author,
            bet=bet_value,
            description="Выберите сторону: **Орёл** или **Решка**?",
        )

        message = await ctx.reply(embed=embed, mention_author=False)
        view = CoinflipView(self, message.id, ctx.author.id)
        view.message = message
        await message.edit(view=view)

        state = CoinflipState(
            user_id=user_id,
            guild_id=guild_id,
            channel_id=message.channel.id,
            bet=bet_value,
            message_id=message.id,
        )
        await self._store_game(message.id, state)

    async def resolve_game(self, message_id: int, choice: str) -> Optional[Embed]:
        state = await self._pop_game(message_id)
        if not state:
            return Embed.error("Сессия монетки не найдена.")

        result = random.choice(("heads", "tails"))
        won = result == choice

        if won:
            await self.economy.add_money(state.user_id, state.guild_id, state.bet * 2, event="coinflip")
            outcome = f"выиграли **{state.bet:,}** {Emojis.MONEY}"
        else:
            outcome = f"проиграли **{state.bet:,}** {Emojis.MONEY}"

        member = await resolve_member(self.bot, state.user_id, state.guild_id)

        choice_name = "орла" if choice == "heads" else "решку"
        result_name = "орла" if result == "heads" else "решку"

        embed = EconomyEmbed.result(
            action="Монетка",
            user=member,
            text=(
                f"вы выбрали **{choice_name}**, "
                f"выпала **{result_name}**. Вы {outcome}."
            ),
        )

        await self.validator.release_game(GAME_NAME, state.user_id, state.guild_id)
        return embed

    async def handle_timeout(self, message_id: int) -> None:
        state = await self._pop_game(message_id)
        if not state:
            return

        await self.economy.add_money(state.user_id, state.guild_id, state.bet)
        await self.validator.release_game(GAME_NAME, state.user_id, state.guild_id)

        channel = self.bot.get_channel(state.channel_id)
        if not isinstance(channel, discord.TextChannel):
            return

        try:
            message = await channel.fetch_message(state.message_id)
        except discord.HTTPException:
            return

        member = await resolve_member(self.bot, state.user_id, state.guild_id)
        embed = EconomyEmbed.result(
            action="Монетка",
            user=member,
            text=f"время выбора вышло. Ставка возвращена.",
        )
        await safe_edit(message, embed=embed, view=None)


    def cog_unload(self) -> None:
        self._games.clear()

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Coinflip(bot))
