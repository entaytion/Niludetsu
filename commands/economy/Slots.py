import asyncio, discord, random
from dataclasses import dataclass
from discord import app_commands
from discord.ext import commands
from Niludetsu import Emojis, Embed, Colors
from Niludetsu.database.supabase_database import database
from Niludetsu.economy.manager import EconomyManager
from Niludetsu.economy.validators import EconomyValidator
from typing import Callable, List, Optional

GAME_NAME = "Слоты"

@dataclass
class SpinContext:
    user_id: int
    guild_id: int
    bet: int
    message: discord.Message
    frames: List[List[List[str]]]
    final_rows: List[List[str]]
    middle_row: List[str]
    won: bool
    multiplier: float
    payout: int
    net_change: int

class SpinAgainView(discord.ui.View):
    def __init__(self, cog: "Slots", user_id: int, guild_id: int, bet: int):
        super().__init__(timeout=120)
        self.cog = cog
        self.user_id = user_id
        self.guild_id = guild_id
        self.bet = bet

    @discord.ui.button(label="Крутить снова", emoji="🔄", style=discord.ButtonStyle.success)
    async def spin_again(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                embed=Embed.error("Эта кнопка принадлежит другому игроку."),
                ephemeral=True,
            )
            return

        await interaction.response.defer()
        await self.cog.start_spin(
            send_callable=lambda **kwargs: interaction.followup.send(**kwargs),
            user_id=self.user_id,
            guild_id=self.guild_id,
            bet=self.bet,
        )

class Slots(commands.Cog):
    """🎰 Слоты: плавная анимация, честные множители и дружелюбный повтор."""

    SYMBOLS: List[str] = ["🍎", "💎", "🍊", "🍇", "🍒", "🍋", "7️⃣", "🎰"]
    MULTIPLIERS = {
        "🍎": 1.5,
        "💎": 2.0,
        "🍊": 1.3,
        "🍇": 1.8,
        "🍒": 1.5,
        "🍋": 1.2,
        "7️⃣": 7.0,
        "🎰": 10.0,
    }
    ANIMATION_DELAYS = [0.22, 0.28, 0.35, 0.45]

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = database
        self.economy = EconomyManager(self.db)
        self.validator = EconomyValidator(self.economy)

    # Команда 
    @commands.hybrid_command(name="slots", description="🎰 Испытать удачу в слотах.")
    @app_commands.describe(bet="🪙 Ставка (минимум 1)")
    async def slots(self, ctx: commands.Context, bet: Optional[str] = None) -> None:
        user_id = ctx.author.id
        guild_id = ctx.guild.id

        valid, bet_value, error_embed = await self.validator.validate_bet(
            bet or "0", str(user_id), str(guild_id)
        )
        if not valid:
            await ctx.reply(embed=error_embed, ephemeral=True)
            return

        if bet_value <= 0:
            await ctx.reply(
                embed=Embed.error("Ставка должна быть положительной."),
                ephemeral=True,
            )
            return

        await self.start_spin(
            send_callable=lambda **kwargs: ctx.reply(**kwargs, mention_author=False),
            user_id=user_id,
            guild_id=guild_id,
            bet=bet_value,
        )

    # Основной процесс 
    async def start_spin(
        self,
        send_callable: Callable[..., discord.Message],
        user_id: int,
        guild_id: int,
        bet: int,
    ) -> None:
        user_key = str(user_id)
        guild_key = str(guild_id)

        claimed, clash_embed = await self.validator.claim_game(GAME_NAME, user_key, guild_key)
        if not claimed:
            await send_callable(embed=clash_embed)
            return

        try:
            removed, fail_msg = await self.economy.remove_money(user_key, guild_key, bet)
            if not removed:
                await send_callable(embed=Embed.error(fail_msg))
                return

            initial_embed = Embed(
                title="🎰 Игровые автоматы",
                description="💫 **Крутим…**",
                color=Colors.PRIMARY,
            )
            message = await send_callable(embed=initial_embed)

            context = await self._perform_spin(user_id, guild_id, bet, message)

            if context is None:
                await message.edit(embed=Embed.error("Не удалось выполнить вращение."))
                await self.economy.add_money(user_key, guild_key, bet)
                return

            for delay, frame in zip(self.ANIMATION_DELAYS, context.frames[:-1]):
                await message.edit(embed=self._build_spin_embed(frame))
                await asyncio.sleep(delay)

            await message.edit(embed=self._build_spin_embed(context.frames[-1]))
            await asyncio.sleep(self.ANIMATION_DELAYS[-1])

            result_embed = await self._build_result_embed(context)
            view = SpinAgainView(self, user_id, guild_id, bet)
            await message.edit(embed=result_embed, view=view)

        except Exception:
            await self.economy.add_money(user_key, guild_key, bet)
            raise
        finally:
            await self.validator.release_game(GAME_NAME, user_key, guild_key)

    async def _perform_spin(
        self,
        user_id: int,
        guild_id: int,
        bet: int,
        message: discord.Message,
    ) -> Optional[SpinContext]:
        final_rows = self._generate_final_rows()
        middle_row = final_rows[1]
        won, multiplier, payout = self._calculate_payout(middle_row, bet)
        net_change = payout - bet if won else -bet

        if won:
            await self.economy.add_money(str(user_id), str(guild_id), payout)

        frames = self._generate_frames(final_rows)
        return SpinContext(
            user_id=user_id,
            guild_id=guild_id,
            bet=bet,
            message=message,
            frames=frames,
            final_rows=final_rows,
            middle_row=middle_row,
            won=won,
            multiplier=multiplier,
            payout=payout,
            net_change=net_change,
        )

    # Генерация и формат 
    def _generate_final_rows(self) -> List[List[str]]:
        return [[random.choice(self.SYMBOLS) for _ in range(3)] for _ in range(3)]

    def _generate_frames(self, final_rows: List[List[str]], prefill: int = 3) -> List[List[List[str]]]:
        buffer = [[random.choice(self.SYMBOLS) for _ in range(3)] for _ in range(prefill)] + final_rows
        frames: List[List[List[str]]] = []
        for idx in range(len(buffer) - 2):
            frames.append(buffer[idx : idx + 3])
        return frames

    def _calculate_payout(self, middle_row: List[str], bet: int) -> tuple[bool, float, int]:
        unique = set(middle_row)
        if len(unique) == 1:
            multiplier = self.MULTIPLIERS[middle_row[0]]
            return True, multiplier, int(round(bet * multiplier))
        if len(unique) == 2:
            for symbol in unique:
                if middle_row.count(symbol) == 2:
                    multiplier = self.MULTIPLIERS[symbol] / 2
                    return True, multiplier, int(round(bet * multiplier))
        return False, 0.0, 0

    def _format_slots(self, rows: List[List[str]]) -> str:
        lines: List[str] = []
        for idx, row in enumerate(rows):
            line = f"| {row[0]} | {row[1]} | {row[2]} |"
            if idx == 1:
                line = f"{line} ←"
            lines.append(line)
        return "\n".join(lines)

    def _build_spin_embed(self, frame: List[List[str]]) -> Embed:
        display = self._format_slots(frame)
        return Embed(
            title="🎰 Игровые автоматы",
            description=f"{display}\n💫 **Крутим…**",
            color=Colors.PRIMARY,
        )

    async def _build_result_embed(self, context: SpinContext) -> Embed:
        display = self._format_slots(context.final_rows)

        if context.won:
            if len(set(context.middle_row)) == 1:
                symbol = context.middle_row[0]
                result_phrase = f"выпал джекпот из трёх {symbol} (x{context.multiplier:g})"
            else:
                symbol = max(set(context.middle_row), key=context.middle_row.count)
                result_phrase = f"выпало два {symbol} (x{context.multiplier:g})"
            color = Colors.SUCCESS
        else:
            result_phrase = "не выпало выигрышной комбинации"
            color = Colors.ERROR

        description = (
            f"{display}\n"
            f"<@{context.user_id}>, вы {'выиграли' if context.won else 'проиграли'} "
            f"**{abs(context.net_change):,}** {Emojis.MONEY}, потому что {result_phrase}."
        )

        embed = Embed(
            title="🎰 Результат слотов",
            description=description,
            color=color,
        )

        avatar = await self._resolve_avatar(context.user_id)
        if avatar:
            embed.set_thumbnail(url=avatar)

        embed = await self._attach_balance_footer(embed, str(context.user_id), str(context.guild_id))
        return embed

    # Утилиты 
    async def _attach_balance_footer(self, embed: Embed, user_id: str, guild_id: str) -> Embed:
        wallet = await self.economy.get_wallet(user_id, guild_id)
        bank = await self.economy.get_bank(user_id, guild_id)
        embed.set_footer(text=f"Кошелёк: {wallet:,} монет • Банк: {bank:,} монет")
        return embed

    async def _resolve_avatar(self, user_id: int) -> Optional[str]:
        for guild in self.bot.guilds:
            member = guild.get_member(user_id)
            if member:
                return member.display_avatar.url
        try:
            user = await self.bot.fetch_user(user_id)
            return user.display_avatar.url
        except discord.HTTPException:
            return None

    def cog_unload(self) -> None:
        pass  # состояние не хранится между играми

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Slots(bot))

