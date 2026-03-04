import asyncio, discord, random, uuid
from dataclasses import dataclass, field
from discord import app_commands
from discord.ext import commands
from Niludetsu import Embed, Colors, Emojis
from Niludetsu.database.supabase_database import database
from Niludetsu.economy.manager import EconomyManager
from Niludetsu.economy.validators import EconomyValidator
from typing import Dict, List, Optional, Tuple

GAME_NAME = "Дуэль"

MAX_HP = 100
ROUND_DELAY = 3.0

WEAPONS: Dict[str, Dict[str, object]] = {
    "sword": {"name": "Меч", "emoji": "⚔️", "dmg": (15, 25), "accuracy": 0.8, "crit": 0.15},
    "bow": {"name": "Лук", "emoji": "🏹", "dmg": (12, 20), "accuracy": 0.85, "crit": 0.2},
    "axe": {"name": "Топор", "emoji": "🪓", "dmg": (18, 30), "accuracy": 0.7, "crit": 0.1},
    "wand": {"name": "Жезл", "emoji": "✨", "dmg": (10, 22), "accuracy": 0.9, "crit": 0.25},
}

ACTION_POOL: List[str] = [
    "целится в голову",
    "стреляет в упор",
    "пытается обойти с фланга",
    "делает резкий выпад",
    "готовит мощную атаку",
    "метит в слабое место",
    "проводит серию быстрых ударов",
    "использует особую технику",
    "идёт на таран",
    "использует окружение",
]

MISS_LINES: List[str] = [
    "промахивается",
    "теряет равновесие",
    "спотыкается",
    "не успевает среагировать",
    "теряет прицел",
]

ACTION_ORDER = ("attack", "defend", "dodge", "counter")

@dataclass
class DuelState:
    duel_id: str
    guild_id: int
    channel_id: int
    message_id: int
    challenger_id: int
    opponent_id: int
    bet: int
    challenger_hp: int = MAX_HP
    opponent_hp: int = MAX_HP
    challenger_weapon: Optional[str] = None
    opponent_weapon: Optional[str] = None
    round_number: int = 0
    last_resolved_round: int = 0
    log: List[str] = field(default_factory=list)

class DuelInviteView(discord.ui.View):
    def __init__(self, cog: "Duel", duel_id: str, challenger_id: int, opponent_id: int, *, timeout: float = 30.0):
        super().__init__(timeout=timeout)
        self.cog = cog
        self.duel_id = duel_id
        self.challenger_id = challenger_id
        self.opponent_id = opponent_id
        self.message: Optional[discord.Message] = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.opponent_id:
            await interaction.response.send_message(
                embed=Embed.error("Ответить на вызов может только приглашённый игрок."),
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self) -> None:
        await self.disable()
        await self.cog.handle_invite_timeout(self.duel_id)

    async def disable(self) -> None:
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass

    @discord.ui.button(label="Принять", style=discord.ButtonStyle.success, emoji="⚔️")
    async def accept(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await interaction.response.defer()
        await self.disable()
        await self.cog.handle_invite_answer(self.duel_id, accepted=True)

    @discord.ui.button(label="Отказаться", style=discord.ButtonStyle.danger, emoji="🏳️")
    async def decline(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await interaction.response.defer()
        await self.disable()
        await self.cog.handle_invite_answer(self.duel_id, accepted=False)

class WeaponSelectView(discord.ui.View):
    def __init__(self, duel: "Duel", duel_id: str, player_id: int, *, timeout: float = 30.0):
        super().__init__(timeout=timeout)
        self.duel = duel
        self.duel_id = duel_id
        self.player_id = player_id
        for key, data in WEAPONS.items():
            button = discord.ui.Button(
                label=data["name"],
                emoji=data["emoji"],
                style=discord.ButtonStyle.secondary,
                custom_id=key,
            )
            button.callback = self._build_callback(key)
            self.add_item(button)

    def _build_callback(self, weapon_key: str):
        async def callback(interaction: discord.Interaction) -> None:
            if interaction.user.id != self.player_id:
                await interaction.response.send_message(
                    embed=Embed.error("Это не ваш выбор оружия."),
                    ephemeral=True,
                )
                return
            await interaction.response.defer()
            await self.duel.handle_weapon_choice(self.duel_id, self.player_id, weapon_key)
            for child in self.children:
                if isinstance(child, discord.ui.Button):
                    child.disabled = True
            if interaction.message:
                try:
                    await interaction.message.edit(view=self)
                except discord.HTTPException:
                    pass

        return callback

class ActionSelectView(discord.ui.View):
    def __init__(self, duel: "Duel", duel_id: str, player_id: int, *, timeout: float = 20.0):
        super().__init__(timeout=timeout)
        self.duel = duel
        self.duel_id = duel_id
        self.player_id = player_id
        for action in ACTION_ORDER:
            label = {
                "attack": "Атака",
                "defend": "Защита",
                "dodge": "Уклонение",
                "counter": "Контратака",
            }[action]
            emoji = {
                "attack": "🗡️",
                "defend": "🛡️",
                "dodge": "🌀",
                "counter": "🔁",
            }[action]
            button = discord.ui.Button(
                label=label,
                emoji=emoji,
                style=discord.ButtonStyle.primary,
                custom_id=action,
            )
            button.callback = self._build_callback(action)
            self.add_item(button)
        random_button = discord.ui.Button(label="Случайно", emoji="🎲", style=discord.ButtonStyle.secondary)
        random_button.callback = self._build_callback("random")
        self.add_item(random_button)

    def _build_callback(self, action_key: str):
        async def callback(interaction: discord.Interaction) -> None:
            if interaction.user.id != self.player_id:
                await interaction.response.send_message(
                    embed=Embed.error("Это не ваш ход."),
                    ephemeral=True,
                )
                return
            await interaction.response.defer()
            await self.duel.handle_action_choice(self.duel_id, self.player_id, action_key)
            for child in self.children:
                if isinstance(child, discord.ui.Button):
                    child.disabled = True
            if interaction.message:
                try:
                    await interaction.message.edit(view=self)
                except discord.HTTPException:
                    pass

        return callback

class Duel(commands.Cog):
    """⚔️ Дуэль: вызов, выбор оружия, поочерёдные раунды и экономические ставки."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = database
        self.economy = EconomyManager(self.db)
        self.validator = EconomyValidator(self.economy)

        self._duels: Dict[str, DuelState] = {}
        self._user_index: Dict[int, str] = {}
        self._lock = asyncio.Lock()
        self._pending_weapon: Dict[Tuple[str, int], str] = {}
        self._pending_actions: Dict[Tuple[str, int], str] = {}

    # Команда 
    @commands.hybrid_command(name="duel", description="[НЕ РАБОТАЕТ] ⚔️ Вызвать игрока на дуэль.")
    @app_commands.describe(
        member="👤 Игрок, которого вы хотите вызвать.",
        bet="🪙 Ставка в монетах.",
    )
    async def duel(
        self,
        ctx: commands.Context,
        member: Optional[discord.Member],
        bet: Optional[str] = None,
    ) -> None:
        if member is None or member.bot:
            await ctx.reply(embed=Embed.error("Укажите живого противника."), ephemeral=True)
            return
        if member.id == ctx.author.id:
            await ctx.reply(embed=Embed.error("Нельзя вызвать на дуэль самого себя."), ephemeral=True)
            return

        challenger_id = ctx.author.id
        opponent_id = member.id
        guild_id = ctx.guild.id
        bet_input = bet or "0"

        valid, bet_value, error_embed = await self.validator.validate_bet(
            bet_input,
            str(challenger_id),
            str(guild_id),
        )
        if not valid:
            await ctx.reply(embed=error_embed, ephemeral=True)
            return

        if bet_value < 0:
            await ctx.reply(embed=Embed.error("Ставка не может быть отрицательной."), ephemeral=True)
            return

        if bet_value > 0:
            opp_valid, _, opp_error = await self.validator.validate_bet(
                str(bet_value),
                str(opponent_id),
                str(guild_id),
            )
            if not opp_valid:
                await ctx.reply(embed=opp_error, ephemeral=True)
                return

        async with self._lock:
            if challenger_id in self._user_index or opponent_id in self._user_index:
                await ctx.reply(embed=Embed.error("Один из игроков уже участвует в другой дуэли."), ephemeral=True)
                return

            duel_id = str(uuid.uuid4())
            state = DuelState(
                duel_id=duel_id,
                guild_id=guild_id,
                channel_id=ctx.channel.id,
                message_id=0,
                challenger_id=challenger_id,
                opponent_id=opponent_id,
                bet=bet_value,
            )
            self._duels[duel_id] = state
            self._user_index[challenger_id] = duel_id
            self._user_index[opponent_id] = duel_id

        claimed, clash = await self.validator.claim_game(GAME_NAME, str(challenger_id), str(guild_id))
        if not claimed:
            await self._cancel_duel(duel_id, silent=True)
            await ctx.reply(embed=clash, ephemeral=True)
            return

        claimed_opp, clash_opp = await self.validator.claim_game(GAME_NAME, str(opponent_id), str(guild_id))
        if not claimed_opp:
            await self.validator.release_game(GAME_NAME, str(challenger_id), str(guild_id))
            await self._cancel_duel(duel_id, silent=True)
            await ctx.reply(embed=clash_opp, ephemeral=True)
            return

        if bet_value > 0:
            removed, fail_msg = await self.economy.remove_money(str(challenger_id), str(guild_id), bet_value)
            if not removed:
                await self._cancel_duel(duel_id, silent=True)
                await self.validator.release_game(GAME_NAME, str(challenger_id), str(guild_id))
                await self.validator.release_game(GAME_NAME, str(opponent_id), str(guild_id))
                await ctx.reply(embed=Embed.error(fail_msg), ephemeral=True)
                return

        invite_embed = Embed(
            title="⚔️ Вызов на дуэль!",
            description=(
                f"<@{challenger_id}> вызывает <@{opponent_id}> на дуэль!\n"
                + (
                    f"{Emojis.MONEY} Ставка: **{bet_value:,}** {Emojis.MONEY}\n"
                    if bet_value
                    else "🎯 Дружеская дуэль без ставки.\n"
                )
                + "⏰ У оппонента 30 секунд, чтобы ответить."
            ),
            color=Colors.PRIMARY,
        )
        invite_embed.set_thumbnail(url=ctx.author.display_avatar.url)

        invite_view = DuelInviteView(self, duel_id, challenger_id, opponent_id)
        message = await ctx.reply(embed=invite_embed, view=invite_view, mention_author=False)
        invite_view.message = message

        async with self._lock:
            state = self._duels.get(duel_id)
            if state:
                state.message_id = message.id

    # Этап принятия 
    async def handle_invite_answer(self, duel_id: str, *, accepted: bool) -> None:
        async with self._lock:
            state = self._duels.get(duel_id)
        if not state:
            return

        channel = self.bot.get_channel(state.channel_id)
        message = None
        if isinstance(channel, discord.TextChannel):
            try:
                message = await channel.fetch_message(state.message_id)
            except discord.HTTPException:
                message = None

        if not accepted:
            if state.bet > 0:
                await self.economy.add_money(str(state.challenger_id), str(state.guild_id), state.bet)
            await self._send_update(
                message,
                Embed.error("🏳️ Оппонент отклонил вызов. Ставка возвращена."),
            )
            await self._cancel_duel(duel_id)
            return

        if state.bet > 0:
            ok, fail_msg = await self.economy.remove_money(str(state.opponent_id), str(state.guild_id), state.bet)
            if not ok:
                await self._send_update(
                    message,
                    Embed.error(f"У оппонента не удалось списать ставку: {fail_msg}"),
                )
                await self.economy.add_money(str(state.challenger_id), str(state.guild_id), state.bet)
                await self._cancel_duel(duel_id)
                return

        await self._send_update(
            message,
            Embed(
                title="⚔️ Дуэль принята!",
                description=(
                    f"<@{state.opponent_id}> принял вызов!\n"
                    "🔧 Теперь оба игрока должны выбрать оружие."
                ),
                color=Colors.SUCCESS,
            ),
        )
        await self._prompt_weapon_choice(state)

    async def handle_invite_timeout(self, duel_id: str) -> None:
        async with self._lock:
            state = self._duels.get(duel_id)
        if not state:
            return

        channel = self.bot.get_channel(state.channel_id)
        message = None
        if isinstance(channel, discord.TextChannel):
            try:
                message = await channel.fetch_message(state.message_id)
            except discord.HTTPException:
                message = None

        if state.bet > 0:
            await self.economy.add_money(str(state.challenger_id), str(state.guild_id), state.bet)
        await self._send_update(
            message,
            Embed.error("⌛ Ответ не получен вовремя. Дуэль отменена, ставка возвращена."),
        )
        await self._cancel_duel(duel_id)

    # Выбор оружия 
    async def _prompt_weapon_choice(self, state: DuelState) -> None:
        channel = self.bot.get_channel(state.channel_id)
        if not isinstance(channel, discord.TextChannel):
            await self._cancel_duel(state.duel_id)
            return

        embed = Embed(
            title="🗡️ Выбор оружия",
            description="Выберите оружие для дуэли. У вас 30 секунд.",
            color=Colors.PRIMARY,
        )

        chal_view = WeaponSelectView(self, state.duel_id, state.challenger_id)
        opp_view = WeaponSelectView(self, state.duel_id, state.opponent_id)

        chal_msg = await channel.send(content=f"<@{state.challenger_id}>, выбирайте:", embed=embed, view=chal_view)
        opp_msg = await channel.send(content=f"<@{state.opponent_id}>, выбирайте:", embed=embed, view=opp_view)

        async def weapon_timeout():
            await asyncio.sleep(30.1)
            async with self._lock:
                st = self._duels.get(state.duel_id)
                if not st or st.challenger_weapon and st.opponent_weapon:
                    return
            await self._send_update(None, Embed.error("⌛ Выбор оружия просрочен. Дуэль отменена, ставки возвращены."))
            if state.bet > 0:
                await self.economy.add_money(str(state.challenger_id), str(state.guild_id), state.bet)
                await self.economy.add_money(str(state.opponent_id), str(state.guild_id), state.bet)
            await self._cancel_duel(state.duel_id)

        asyncio.create_task(weapon_timeout())

    async def handle_weapon_choice(self, duel_id: str, player_id: int, weapon_key: str) -> None:
        async with self._lock:
            state = self._duels.get(duel_id)
            if not state:
                return
            if player_id == state.challenger_id:
                state.challenger_weapon = weapon_key
            elif player_id == state.opponent_id:
                state.opponent_weapon = weapon_key

            both_ready = state.challenger_weapon and state.opponent_weapon

        if both_ready:
            channel = self.bot.get_channel(state.channel_id)
            if isinstance(channel, discord.TextChannel):
                try:
                    await channel.send(
                        embed=Embed(
                            title="⚔️ Оружие выбрано!",
                            description=(
                                f"<@{state.challenger_id}> выбрал {WEAPONS[state.challenger_weapon]['emoji']}\n"
                                f"{WEAPONS[state.challenger_weapon]['name']}\n"
                                f"<@{state.opponent_id}> выбрал {WEAPONS[state.opponent_weapon]['emoji']}\n"
                                f"{WEAPONS[state.opponent_weapon]['name']}"
                            ),
                            color=Colors.SUCCESS,
                        )
                    )
                except discord.HTTPException:
                    pass
            await asyncio.sleep(2)
            await self._start_round(state.duel_id)

    # Раунды 
    async def _start_round(self, duel_id: str) -> None:
        async with self._lock:
            state = self._duels.get(duel_id)
        if not state:
            return

        state.round_number += 1
        channel = self.bot.get_channel(state.channel_id)
        if not isinstance(channel, discord.TextChannel):
            await self._cancel_duel(duel_id)
            return

        embed = Embed(
            title=f"⚔️ Раунд {state.round_number}",
            description=(
                f"**Игрок 1:** <@{state.challenger_id}> — {state.challenger_hp}❤️ "
                f"({WEAPONS[state.challenger_weapon]['emoji']} {WEAPONS[state.challenger_weapon]['name']})\n"
                f"**Игрок 2:** <@{state.opponent_id}> — {state.opponent_hp}❤️ "
                f"({WEAPONS[state.opponent_weapon]['emoji']} {WEAPONS[state.opponent_weapon]['name']})\n"
                "Выберите действие:"
            ),
            color=Colors.PRIMARY,
        )

        chal_view = ActionSelectView(self, duel_id, state.challenger_id)
        opp_view = ActionSelectView(self, duel_id, state.opponent_id)

        chal_msg = await channel.send(content=f"<@{state.challenger_id}>:", embed=embed, view=chal_view)
        opp_msg = await channel.send(content=f"<@{state.opponent_id}>:", embed=embed, view=opp_view)

        current_round = state.round_number

        async def actions_timeout() -> None:
            await asyncio.sleep(20.1)
            async with self._lock:
                active_state = self._duels.get(duel_id)
                if not active_state:
                    return
                if active_state.last_resolved_round >= current_round:
                    return
                self._pending_actions.pop((duel_id, active_state.challenger_id), None)
                self._pending_actions.pop((duel_id, active_state.opponent_id), None)
            await self._send_update(
                None,
                Embed.error("⌛ Кто-то не выбрал действие вовремя. Дуэль завершена без победителя."),
            )
            await self._finish_duel(active_state, winner_id=None, timeout=True)

        asyncio.create_task(actions_timeout())

    async def handle_action_choice(self, duel_id: str, player_id: int, action_key: str) -> None:
        if action_key == "random":
            action_key = random.choice(ACTION_ORDER)

        async with self._lock:
            if duel_id not in self._duels:
                return
            self._pending_actions[(duel_id, player_id)] = action_key
            state = self._duels[duel_id]
            first = self._pending_actions.get((duel_id, state.challenger_id))
            second = self._pending_actions.get((duel_id, state.opponent_id))
            if not (first and second):
                return
            state.last_resolved_round = state.round_number
            self._pending_actions.pop((duel_id, state.challenger_id), None)
            self._pending_actions.pop((duel_id, state.opponent_id), None)
        await self._resolve_round(state, first, second)

    async def _resolve_round(self, state: DuelState, challenger_action: str, opponent_action: str) -> None:
        log_lines: List[str] = []
        for attacker, action, weapon_key, defender in (
            (
                state.challenger_id,
                challenger_action,
                state.challenger_weapon,
                state.opponent_id,
            ),
            (
                state.opponent_id,
                opponent_action,
                state.opponent_weapon,
                state.challenger_id,
            ),
        ):
            weapon = WEAPONS[weapon_key]
            if random.random() <= weapon["accuracy"]:
                damage = random.randint(*weapon["dmg"])
                critical = random.random() <= weapon["crit"]
                if critical:
                    damage = int(damage * 1.5)
                target_hp_attr = "opponent_hp" if defender == state.opponent_id else "challenger_hp"
                setattr(state, target_hp_attr, max(0, getattr(state, target_hp_attr) - damage))
                line = (
                    f"<@{attacker}> {random.choice(ACTION_POOL)} и наносит **{damage}**"
                    f"{'🔥' if critical else ''} урона <@{defender}>!"
                )
            else:
                line = f"<@{attacker}> {random.choice(ACTION_POOL)}, но {random.choice(MISS_LINES)}!"
            log_lines.append(line)
            if state.challenger_hp == 0 or state.opponent_hp == 0:
                break

        state.log.extend(log_lines)
        channel = self.bot.get_channel(state.channel_id)
        if isinstance(channel, discord.TextChannel):
            try:
                await channel.send(
                    embed=Embed(
                        title=f"⚔️ Итоги раунда {state.round_number}",
                        description="\n".join(log_lines)
                        + "\n"
                        + f"💚 <@{state.challenger_id}>: {state.challenger_hp}❤️\n"
                        + f"💙 <@{state.opponent_id}>: {state.opponent_hp}❤️",
                        color=Colors.PRIMARY,
                    )
                )
            except discord.HTTPException:
                pass

        if state.challenger_hp == 0 or state.opponent_hp == 0:
            winner = state.challenger_id if state.opponent_hp == 0 else state.opponent_id
            await self._finish_duel(state, winner_id=winner)
            return

        await asyncio.sleep(ROUND_DELAY)
        await self._start_round(state.duel_id)

    # Завершение 
    async def _finish_duel(self, state: DuelState, *, winner_id: Optional[int], timeout: bool = False) -> None:
        channel = self.bot.get_channel(state.channel_id)
        embed: Embed

        if timeout or winner_id is None:
            embed = Embed.error("Дуэль завершилась без победителя. Ставки возвращены.")
            if state.bet > 0:
                await self.economy.add_money(str(state.challenger_id), str(state.guild_id), state.bet)
                await self.economy.add_money(str(state.opponent_id), str(state.guild_id), state.bet)
        else:
            loser_id = state.opponent_id if winner_id == state.challenger_id else state.challenger_id
            winnings = state.bet * 2
            if winnings > 0:
                await self.economy.add_money(str(winner_id), str(state.guild_id), winnings)

            embed = Embed(
                title="🏆 Дуэль завершена!",
                description=(
                    f"**Победитель:** <@{winner_id}>\n"
                    f"**Проигравший:** <@{loser_id}>\n"
                    + (
                        f"**Выигрыш:** {winnings:,} {Emojis.MONEY}\n"
                        if winnings
                        else "🎯 Дружеская дуэль без ставок."
                    )
                    + "\n"
                    + "\n".join(state.log[-6:])
                ),
                color=Colors.SUCCESS,
            )
            embed = await self._attach_balance_footer(embed, str(winner_id), str(state.guild_id))

        if isinstance(channel, discord.TextChannel):
            try:
                await channel.send(embed=embed)
            except discord.HTTPException:
                pass

        await self._cancel_duel(state.duel_id)

    async def _cancel_duel(self, duel_id: str, *, silent: bool = False) -> None:
        async with self._lock:
            state = self._duels.pop(duel_id, None)
            if not state:
                return
            self._user_index.pop(state.challenger_id, None)
            self._user_index.pop(state.opponent_id, None)

        await self.validator.release_game(GAME_NAME, str(state.challenger_id), str(state.guild_id))
        await self.validator.release_game(GAME_NAME, str(state.opponent_id), str(state.guild_id))
        if not silent and state.bet > 0:
            await self.economy.add_money(str(state.challenger_id), str(state.guild_id), state.bet)

    # Утилиты 
    async def _send_update(self, message: Optional[discord.Message], embed: Embed) -> None:
        if message:
            try:
                await message.edit(embed=embed, view=None)
            except discord.HTTPException:
                pass
        else:
            guild = self.bot.get_guild(embed.guild_id) if hasattr(embed, "guild_id") else None
            _ = guild  # заглушка

    async def _attach_balance_footer(self, embed: Embed, user_id: str, guild_id: str) -> Embed:
        wallet = await self.economy.get_wallet(user_id, guild_id)
        bank = await self.economy.get_bank(user_id, guild_id)
        embed.set_footer(text=f"Кошелёк: {wallet:,} {Emojis.MONEY} • Банк: {bank:,} {Emojis.MONEY}")
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
        self._duels.clear()
        self._user_index.clear()

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Duel(bot))

