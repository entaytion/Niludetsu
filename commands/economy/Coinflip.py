import asyncio, discord, random
from dataclasses import dataclass
from discord import app_commands
from discord.ext import commands
from Niludetsu import Emojis, Embed, Colors
from Niludetsu.database.supabase_database import database
from Niludetsu.economy.manager import EconomyManager
from Niludetsu.economy.validators import EconomyValidator
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

class CoinflipView(discord.ui.View):
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
        await self.disable_buttons()
        await self.cog.handle_timeout(self.game_id)

    async def disable_buttons(self) -> None:
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass

    @discord.ui.button(label="Орёл", style=discord.ButtonStyle.secondary, emoji="🦅")
    async def heads(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.process_choice(interaction, "heads")

    @discord.ui.button(label="Решка", style=discord.ButtonStyle.secondary, emoji="⚪")
    async def tails(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.process_choice(interaction, "tails")

    async def process_choice(self, interaction: discord.Interaction, choice: str) -> None:
        await interaction.response.defer()
        await self.disable_buttons()
        embed = await self.cog.resolve_game(self.game_id, choice)
        if embed and self.message:
            try:
                await self.message.edit(embed=embed, view=None)
            except discord.HTTPException:
                pass

class Coinflip(commands.Cog):
    """🪙 Монетка: ставка х2 с учётом экономики и блокировкой мультисессий."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = database
        self.economy = EconomyManager(self.db)
        self.validator = EconomyValidator(self.economy)

        self._games: Dict[int, CoinflipState] = {}
        self._lock = asyncio.Lock()

    # Хранилище состояния 
    async def _store_game(self, message_id: int, state: CoinflipState) -> None:
        async with self._lock:
            self._games[message_id] = state

    async def _pop_game(self, message_id: int) -> Optional[CoinflipState]:
        async with self._lock:
            return self._games.pop(message_id, None)

    # Команда 
    @commands.hybrid_command(
        name="coinflip",
        aliases=("монетка",),
        description="🪙 Сыграть в монетку и удвоить ставку.",
    )
    @app_commands.describe(bet="🪙 Сумма ставки")
    async def coinflip(self, ctx: commands.Context, bet: Optional[str] = None) -> None:
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

        removed, error_text = await self.economy.remove_money(user_id, guild_id, bet_value)
        if not removed:
            await self.validator.release_game(GAME_NAME, user_id, guild_id)
            await ctx.reply(embed=Embed.error(error_text), ephemeral=True)
            return

        await ctx.defer(ephemeral=False)

        embed = Embed(
            title="🪙 Игра в монетку",
            description=(
                f"Ставка: **{bet_value:,}** {Emojis.MONEY}\n"
                "Выберите сторону: **Орёл** или **Решка**?"
            ),
            color=Colors.PRIMARY,
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)

        message = await ctx.reply(embed=embed, mention_author=False)
        view = CoinflipView(self, message.id, ctx.author.id)  # ← game_id совпадает с message.id
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

    # Игровая логика 
    async def resolve_game(self, message_id: int, choice: str) -> Optional[Embed]:
        state = await self._pop_game(message_id)
        if not state:
            return Embed.error("Сессия монетки не найдена.")

        result = random.choice(("heads", "tails"))
        won = result == choice

        if won:
            await self.economy.add_money(state.user_id, state.guild_id, state.bet * 2)
            outcome = f"🎉 Победа! Вы забрали **{state.bet:,}** {Emojis.MONEY} сверху."
            color = Colors.SUCCESS
        else:
            outcome = f"😢 Поражение. Ставка **{state.bet:,}** {Emojis.MONEY} сгорела."
            color = Colors.ERROR

        embed = Embed(
            title="🪙 Результат монетки",
            description=(
                f"<@{state.user_id}> выбрал **{'орла' if choice == 'heads' else 'решку'}**.\n"
                f"Монета показала **{'орла' if result == 'heads' else 'решку'}**.\n"
                f"{outcome}"
            ),
            color=color,
        )

        avatar = await self._resolve_avatar(state.user_id)
        if avatar:
            embed.set_thumbnail(url=avatar)
        embed = await self._attach_balance_footer(embed, state.user_id, state.guild_id)

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

        embed = Embed.error("⏳ Время выбора вышло. Ставка возвращена.")
        embed = await self._attach_balance_footer(embed, state.user_id, state.guild_id)
        try:
            await message.edit(embed=embed, view=None)
        except discord.HTTPException:
            pass

    # Утилиты 
    async def _attach_balance_footer(self, embed: Embed, user_id: str, guild_id: str) -> Embed:
        wallet = await self.economy.get_wallet(user_id, guild_id)
        bank = await self.economy.get_bank(user_id, guild_id)
        embed.set_footer(text=f"Кошелёк: {wallet:,} {Emojis.MONEY} • Банк: {bank:,} {Emojis.MONEY}")
        return embed

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

    def cog_unload(self) -> None:
        self._games.clear()

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Coinflip(bot))

