import discord
from discord import app_commands
from discord.ext import commands
from Niludetsu import Embed, Colors, Emojis
from Niludetsu.database.supabase_database import database
from Niludetsu.economy.manager import EconomyManager
from Niludetsu.tools.Time import TimeService
from typing import Dict, List, Optional

PAGE_SIZE = 10

EVENT_LABELS: Dict[str, str] = {
    "daily": "Ежедневка",
    "work": "Подработка",
    "slut": "Заработок",
    "slut_penalty": "Штраф",
    "rob": "Ограбление",
    "rob_penalty": "Штраф",
    "pay": "Перевод",
    "deposit": "Депозит",
    "withdraw": "Снятие",
    "withdraw_family": "Семейный счёт",
    "coinflip": "Монетка",
    "slots": "Слоты",
    "roulette": "Рулетка",
    "blackjack": "Блекджек",
    "duel": "Дуэль",
    "income": "Доход с роли",
    "shop": "Покупка",
    "refund": "Возврат",
    "quest_reward": "Квест",
}

FILTER_MAP: Dict[str, Optional[List[str]]] = {
    "all": None,
    "income": ["daily", "work", "slut", "income", "quest_reward"],
    "games": ["coinflip", "slots", "roulette", "blackjack"],
    "transfers": ["pay", "rob", "rob_penalty", "duel"],
    "bank": ["deposit", "withdraw", "withdraw_family"],
}

FILTER_LABELS: Dict[str, str] = {
    "all": "Все",
    "income": "Доход",
    "games": "Игры",
    "transfers": "Переводы",
    "bank": "Банк",
}


EVENT_ICONS: Dict[str, str] = {
    "daily": "🎁",
    "work": "🛠️",
    "slut": "💋",
    "slut_penalty": "⚠️",
    "rob": "🔫",
    "rob_penalty": "⚠️",
    "pay": "💸",
    "deposit": "🏦",
    "withdraw": "🏦",
    "withdraw_family": "👨‍👩‍👧",
    "coinflip": "🪙",
    "slots": "🎰",
    "roulette": "🎡",
    "blackjack": "🃏",
    "duel": "⚔️",
    "income": "💎",
    "shop": "🛒",
    "refund": "↩️",
    "quest_reward": "📜",
}

_DOT = "・"


def _format_row(tx: dict, time_svc: TimeService) -> str:
    amount = tx["amount"]
    event = tx["event"]
    icon = EVENT_ICONS.get(event, "📌")
    label = EVENT_LABELS.get(event, event)

    if amount >= 0:
        amount_str = f"**+{amount:,}**"
    else:
        amount_str = f"**{amount:,}**"

    created = time_svc.ensure_datetime(tx.get("created_at"))
    time_str = f"`{created.format('HH:mm')}`" if created else ""

    related = tx.get("related_user_id")
    related_str = ""
    if related:
        if amount < 0:
            related_str = f" → <@{related}>"
        else:
            related_str = f" ← <@{related}>"

    return f"{icon} **{label}**{related_str}{_DOT}{amount_str} {Emojis.MONEY}{_DOT}{time_str}"


class TransactionsPaginator(discord.ui.View):
    def __init__(
        self,
        cog: "Transactions",
        target_id: str,
        guild_id: str,
        invoker_id: int,
        display_name: str,
        *,
        avatar_url: Optional[str] = None,
        timeout: float = 120.0,
    ):
        super().__init__(timeout=timeout)
        self.cog = cog
        self.target_id = target_id
        self.guild_id = guild_id
        self.invoker_id = invoker_id
        self.display_name = display_name
        self.avatar_url = avatar_url
        self.page = 0
        self.total = 0
        self.filter_key = "all"
        self.message: Optional[discord.Message] = None

    @property
    def max_page(self) -> int:
        return max(0, (self.total - 1) // PAGE_SIZE)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.invoker_id:
            await interaction.response.send_message(
                embed=Embed.error("Эта панель принадлежит другому пользователю."),
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self) -> None:
        for child in self.children:
            if hasattr(child, "disabled"):
                child.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass

    async def fetch_and_edit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        embed = await self.cog.build_embed(
            self.target_id,
            self.guild_id,
            self.display_name,
            page=self.page,
            events=FILTER_MAP[self.filter_key],
            paginator=self,
            avatar_url=self.avatar_url,
        )
        self._update_buttons()
        await interaction.message.edit(embed=embed, view=self)

    def _update_buttons(self) -> None:
        self.btn_prev.disabled = self.page <= 0
        self.btn_label.label = f"{self.page + 1}/{self.max_page + 1}"
        self.btn_next.disabled = self.page >= self.max_page

    @discord.ui.button(label="◀", style=discord.ButtonStyle.secondary, row=0)
    async def btn_prev(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        self.page = max(0, self.page - 1)
        await self.fetch_and_edit(interaction)

    @discord.ui.button(label="1/1", style=discord.ButtonStyle.secondary, disabled=True, row=0)
    async def btn_label(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        pass

    @discord.ui.button(label="▶", style=discord.ButtonStyle.secondary, row=0)
    async def btn_next(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        self.page = min(self.max_page, self.page + 1)
        await self.fetch_and_edit(interaction)

    @discord.ui.select(
        placeholder="Фильтр",
        options=[
            discord.SelectOption(label=FILTER_LABELS[k], value=k, default=(k == "all"))
            for k in FILTER_LABELS
        ],
        row=1,
    )
    async def filter_select(self, interaction: discord.Interaction, select: discord.ui.Select) -> None:
        self.filter_key = select.values[0]
        self.page = 0
        for opt in select.options:
            opt.default = opt.value == self.filter_key
        await self.fetch_and_edit(interaction)


class Transactions(commands.Cog):
    """Просмотр истории транзакций."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = database
        self.economy = EconomyManager(self.db)
        self.time = TimeService()

    async def build_embed(
        self,
        user_id: str,
        guild_id: str,
        display_name: str,
        *,
        page: int = 0,
        events: Optional[List[str]] = None,
        paginator: Optional[TransactionsPaginator] = None,
        avatar_url: Optional[str] = None,
    ) -> Embed:
        offset = page * PAGE_SIZE
        rows, total = await self.db.get_transactions(
            user_id, guild_id, limit=PAGE_SIZE, offset=offset, events=events,
        )

        if paginator:
            paginator.total = total

        if not rows:
            embed = Embed(
                title=f"📋 Транзакции {display_name}",
                description="История пуста.",
                color=Colors.PRIMARY,
            )
            if avatar_url:
                embed.set_thumbnail(url=avatar_url)
            return embed

        lines = [_format_row(tx, self.time) for tx in rows]
        max_page = max(0, (total - 1) // PAGE_SIZE)

        filter_label = FILTER_LABELS.get(paginator.filter_key, "Все") if paginator else "Все"

        embed = Embed(
            title=f"📋 Транзакции {display_name}",
            description="\n".join(lines),
            color=Colors.PRIMARY,
        )
        if avatar_url:
            embed.set_thumbnail(url=avatar_url)
        embed.set_footer(text=f"Страница {page + 1}/{max_page + 1} • Фильтр: {filter_label} • Всего: {total:,}")
        return embed

    @commands.hybrid_command(
        name="transactions",
        aliases=("tx", "транзакции"),
        description="📋 Показать историю транзакций",
    )
    @app_commands.describe(user="👤 Кого посмотреть (по умолчанию — вы)")
    async def transactions(self, ctx: commands.Context, user: Optional[discord.Member] = None) -> None:
        if ctx.interaction and not ctx.interaction.response.is_done():
            await ctx.defer()
        target = user or ctx.author
        target_id = str(target.id)
        guild_id = str(ctx.guild.id)

        avatar_url = target.display_avatar.url
        paginator = TransactionsPaginator(
            self, target_id, guild_id, ctx.author.id, target.display_name,
            avatar_url=avatar_url,
        )
        embed = await self.build_embed(
            target_id, guild_id, target.display_name, paginator=paginator,
            avatar_url=avatar_url,
        )
        paginator._update_buttons()
        message = await ctx.reply(embed=embed, view=paginator, mention_author=False)
        paginator.message = message


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Transactions(bot))
