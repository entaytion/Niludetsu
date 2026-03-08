import asyncio, discord
from discord import app_commands
from discord.ext import commands
from Niludetsu import Embed, Colors, Emojis
from Niludetsu.database.supabase_database import database
from Niludetsu.economy.manager import EconomyManager
from typing import Dict, Optional, Tuple

CHOICES = {
    "rock": {"name": "Камень", "emoji": "🪨", "beats": "scissors"},
    "scissors": {"name": "Ножницы", "emoji": "✂️", "beats": "paper"},
    "paper": {"name": "Бумага", "emoji": "📄", "beats": "rock"},
}

GAME_TIMEOUT = 60.0


class RPSPickView(discord.ui.View):
    """Личное меню выбора для одного игрока."""

    def __init__(self, game: "RPSGame", player_id: int) -> None:
        super().__init__(timeout=GAME_TIMEOUT)
        self.game = game
        self.player_id = player_id
        self.picked = False

    async def _pick(self, interaction: discord.Interaction, choice: str) -> None:
        if interaction.user.id != self.player_id:
            return
        if self.picked:
            await interaction.response.send_message(
                embed=Embed.error("Ты уже выбрал!"), ephemeral=True,
            )
            return

        self.picked = True
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(
            embed=Embed(
                description=f"Ты выбрал **{CHOICES[choice]['emoji']} {CHOICES[choice]['name']}**. Ожидание соперника...",
                color=Colors.PRIMARY,
            ),
            view=self,
        )
        await self.game.register_choice(self.player_id, choice)

    @discord.ui.button(label="Камень", emoji="🪨", style=discord.ButtonStyle.secondary)
    async def rock(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self._pick(interaction, "rock")

    @discord.ui.button(label="Ножницы", emoji="✂️", style=discord.ButtonStyle.secondary)
    async def scissors(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self._pick(interaction, "scissors")

    @discord.ui.button(label="Бумага", emoji="📄", style=discord.ButtonStyle.secondary)
    async def paper(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self._pick(interaction, "paper")

    async def on_timeout(self) -> None:
        await self.game.handle_timeout(self.player_id)


class RPSChallengeView(discord.ui.View):
    """Кнопка принятия/отклонения вызова."""

    def __init__(self, game: "RPSGame") -> None:
        super().__init__(timeout=GAME_TIMEOUT)
        self.game = game

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.game.challenger_id:
            await interaction.response.send_message(
                embed=Embed.error("Ты не можешь принять свой же вызов!"), ephemeral=True,
            )
            return False
        if interaction.user.id != self.game.target_id:
            await interaction.response.send_message(
                embed=Embed.error("Этот вызов не для тебя!"), ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(label="Принять", emoji="✅", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        await self.game.start_picks(interaction)

    @discord.ui.button(label="Отклонить", emoji="❌", style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(
            embed=Embed(
                description=f"<@{self.game.target_id}> отклонил вызов.",
                color=Colors.ERROR,
            ),
            view=self,
        )
        await self.game.cleanup()

    async def on_timeout(self) -> None:
        await self.game.handle_challenge_timeout()


class RPSGame:
    """Управляет одной сессией RPS."""

    def __init__(
        self,
        cog: "RPS",
        channel: discord.TextChannel,
        challenger: discord.Member,
        target: discord.Member,
        bet: int,
    ) -> None:
        self.cog = cog
        self.channel = channel
        self.challenger_id = challenger.id
        self.target_id = target.id
        self.challenger_name = challenger.display_name
        self.target_name = target.display_name
        self.bet = bet
        self.guild_id = channel.guild.id

        self._choices: Dict[int, str] = {}
        self._lock = asyncio.Lock()
        self._challenge_message: Optional[discord.Message] = None
        self._resolved = False

    def _game_key(self) -> Tuple[int, int, int]:
        return (min(self.challenger_id, self.target_id), max(self.challenger_id, self.target_id), self.guild_id)

    async def send_challenge(self, ctx: commands.Context) -> None:
        bet_line = f"\nСтавка: **{self.bet:,}** {Emojis.MONEY}" if self.bet else ""
        embed = Embed(
            title="✊ Камень-Ножницы-Бумага",
            description=(
                f"**{self.challenger_name}** вызывает **{self.target_name}** на дуэль!{bet_line}\n\n"
                f"<@{self.target_id}>, принимаешь?"
            ),
            color=Colors.PRIMARY,
        )
        view = RPSChallengeView(self)
        self._challenge_message = await ctx.reply(embed=embed, view=view, mention_author=False)

    async def start_picks(self, interaction: discord.Interaction) -> None:
        """Отправляет каждому игроку личное сообщение с кнопками выбора."""
        pick_embed = Embed(
            description="Выбери свой ход:",
            color=Colors.PRIMARY,
        )

        # Challenger
        view1 = RPSPickView(self, self.challenger_id)
        try:
            challenger = interaction.guild.get_member(self.challenger_id)
            if challenger:
                await challenger.send(embed=pick_embed, view=view1)
        except discord.HTTPException:
            pass

        # Target
        view2 = RPSPickView(self, self.target_id)
        try:
            await interaction.user.send(embed=pick_embed, view=view2)
        except discord.HTTPException:
            pass

        # Обновляем сообщение в канале
        if self._challenge_message:
            await self._challenge_message.edit(
                embed=Embed(
                    title="✊ Камень-Ножницы-Бумага",
                    description=(
                        f"**{self.challenger_name}** vs **{self.target_name}**\n"
                        "Оба игрока выбирают... ⏳"
                    ),
                    color=Colors.PRIMARY,
                ),
            )

    async def register_choice(self, player_id: int, choice: str) -> None:
        async with self._lock:
            self._choices[player_id] = choice
            if len(self._choices) == 2:
                await self._resolve()

    async def _resolve(self) -> None:
        if self._resolved:
            return
        self._resolved = True

        c1 = self._choices[self.challenger_id]
        c2 = self._choices[self.target_id]

        c1_info = CHOICES[c1]
        c2_info = CHOICES[c2]

        if c1 == c2:
            result_text = "🤝 **Ничья!**"
            color = Colors.PRIMARY
            winner_id = None
        elif c1_info["beats"] == c2:
            result_text = f"🎉 **{self.challenger_name}** побеждает!"
            color = Colors.SUCCESS
            winner_id = self.challenger_id
        else:
            result_text = f"🎉 **{self.target_name}** побеждает!"
            color = Colors.SUCCESS
            winner_id = self.target_id

        desc_lines = [
            f"{self.challenger_name}: {c1_info['emoji']} **{c1_info['name']}**",
            f"{self.target_name}: {c2_info['emoji']} **{c2_info['name']}**",
            "",
            result_text,
        ]

        # Экономика
        if self.bet and winner_id:
            loser_id = self.target_id if winner_id == self.challenger_id else self.challenger_id
            await self.cog.economy.add_money(str(winner_id), str(self.guild_id), self.bet, event="rps")
            await self.cog.economy.remove_money(str(loser_id), str(self.guild_id), self.bet, event="rps")
            desc_lines.append(f"\n💰 **{self.bet:,}** {Emojis.MONEY} переходят победителю!")
        elif self.bet and winner_id is None:
            # Ничья — вернуть ставки (ничего не списываем, т.к. не списывали заранее)
            pass

        embed = Embed(
            title="✊ Результат",
            description="\n".join(desc_lines),
            color=color,
        )

        if self._challenge_message:
            try:
                await self._challenge_message.edit(embed=embed, view=None)
            except discord.HTTPException:
                pass

        await self.cleanup()

    async def handle_timeout(self, player_id: int) -> None:
        async with self._lock:
            if self._resolved:
                return
            self._resolved = True

        name = self.challenger_name if player_id == self.challenger_id else self.target_name
        if self._challenge_message:
            try:
                await self._challenge_message.edit(
                    embed=Embed(
                        description=f"⏳ **{name}** не успел выбрать. Игра отменена.",
                        color=Colors.ERROR,
                    ),
                    view=None,
                )
            except discord.HTTPException:
                pass
        await self.cleanup()

    async def handle_challenge_timeout(self) -> None:
        if self._resolved:
            return
        self._resolved = True
        if self._challenge_message:
            try:
                await self._challenge_message.edit(
                    embed=Embed(
                        description=f"⏳ <@{self.target_id}> не ответил на вызов.",
                        color=Colors.ERROR,
                    ),
                    view=None,
                )
            except discord.HTTPException:
                pass
        await self.cleanup()

    async def cleanup(self) -> None:
        self.cog._active_games.pop(self._game_key(), None)


class RPS(commands.Cog):
    """✊ Камень-Ножницы-Бумага: PvP на деньги или просто так."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = database
        self.economy = EconomyManager(self.db)
        self._active_games: Dict[Tuple[int, int, int], RPSGame] = {}

    @commands.hybrid_command(
        name="rps",
        aliases=("кнб",),
        description="✊ Камень-Ножницы-Бумага",
    )
    @app_commands.describe(
        user="Против кого играть",
        bet="Ставка (необязательно)",
    )
    async def rps(self, ctx: commands.Context, user: discord.Member, bet: Optional[str] = None) -> None:
        if ctx.interaction and not ctx.interaction.response.is_done():
            await ctx.defer()

        if user.id == ctx.author.id:
            return await ctx.reply(embed=Embed.error("Нельзя играть с самим собой!"), ephemeral=True)
        if user.bot:
            return await ctx.reply(embed=Embed.error("Нельзя играть с ботом!"), ephemeral=True)

        guild_id = ctx.guild.id
        game_key = (min(ctx.author.id, user.id), max(ctx.author.id, user.id), guild_id)

        if game_key in self._active_games:
            return await ctx.reply(
                embed=Embed.error("Между вами уже идёт игра!"), ephemeral=True,
            )

        # Парсим ставку
        bet_value = 0
        if bet is not None:
            raw = str(bet).strip()
            if not raw.isdigit() or int(raw) < 1:
                return await ctx.reply(
                    embed=Embed.error(f"Некорректная ставка! Пример: `/rps @user 100`"),
                    ephemeral=True,
                )
            bet_value = int(raw)

            # Проверяем баланс обоих
            for player in (ctx.author, user):
                wallet = await self.economy.get_wallet(str(player.id), str(guild_id))
                if wallet < bet_value:
                    return await ctx.reply(
                        embed=Embed.error(
                            f"У **{player.display_name}** недостаточно средств! "
                            f"Баланс: **{wallet:,}** {Emojis.MONEY}, нужно: **{bet_value:,}** {Emojis.MONEY}"
                        ),
                        ephemeral=True,
                    )

        game = RPSGame(self, ctx.channel, ctx.author, user, bet_value)
        self._active_games[game_key] = game
        await game.send_challenge(ctx)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RPS(bot))
