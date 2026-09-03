import discord, math
from Niludetsu import Embed, Emojis
from discord import app_commands
from discord.ext import commands
from Niludetsu.moderation.checks import moderationcommand
from Niludetsu.moderation.system.rudiments import RudimentsSystem
from Niludetsu.locale import _, DEFAULT_LOCALE

PUNISHMENT_TYPES = (
    ("warn", "Предупреждения", Emojis.WARN),
    ("mute", "Муты", Emojis.MUTE),
    ("ban", "Баны", Emojis.BAN),
)

PUNISHMENT_LABELS = {
    "warn": "варн",
    "mute": "мут",
    "ban": "бан",
}

PAGE_SIZE = 5

class RudimentSelect(discord.ui.Select):
    def __init__(self, current: str, available_types: list[str]) -> None:
        options = []

        for value, label, emoji in PUNISHMENT_TYPES:
            if value in available_types:
                options.append(
                    discord.SelectOption(
                        label=label,
                        value=value,
                        emoji=emoji,
                        default=value == current,
                    )
                )

        if len(available_types) > 1:
            options.append(
                discord.SelectOption(
                    label=DEFAULT_LOCALE.get("moderation", {}).get("rudiment_select_all", "Все типы"),
                    value="all",
                    emoji="📚",
                    default="all" == current,
                )
            )

        super().__init__(
            placeholder=DEFAULT_LOCALE.get("moderation", {}).get("rudiment_placeholder", "🎛️ Выберите тип нарушения"),
            min_values=1,
            max_values=1,
            options=options,
            row=0,
        )

    def update_default(self, current: str) -> None:
        for option in self.options:
            option.default = option.value == current

    async def callback(self, interaction: discord.Interaction) -> None:
        view: "RudimentView" = self.view  # type: ignore[assignment]
        await view.handle_selection(interaction, self.values[0])

class PageButton(discord.ui.Button):
    def __init__(self, direction: int) -> None:
        label = DEFAULT_LOCALE.get("moderation", {}).get("rudiment_page_prev") if direction < 0 else DEFAULT_LOCALE.get("moderation", {}).get("rudiment_page_next")
        emoji = "◀️" if direction < 0 else "▶️"
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label=label or ("Назад" if direction < 0 else "Вперёд"),
            emoji=emoji,
            row=1,
        )
        self.direction = direction

    async def callback(self, interaction: discord.Interaction) -> None:
        view: "RudimentView" = self.view  # type: ignore[assignment]
        await view.change_page(interaction, self.direction)

class RudimentView(discord.ui.View):
    def __init__(
        self,
        *,
        system: RudimentsSystem,
        member: discord.Member,
        include_inactive: bool = False,
        statistics: dict[str, int] | None = None,
    ) -> None:
        super().__init__(timeout=180)
        self.system = system
        self.member = member
        self.include_inactive = include_inactive
        self.statistics = statistics or {}
        self.available_types = [k for k, v in self.statistics.items() if v > 0]
        self.current_action = "summary"
        self.page = 1
        self._records_cache: dict[str, list] = {}

        if self.available_types:
            self.selector = RudimentSelect(self.current_action, self.available_types)
            self.add_item(self.selector)

        self.prev_button = PageButton(-1)
        self.next_button = PageButton(1)
        self.message: discord.Message | None = None

    async def build_embed(self) -> Embed:
        if self.current_action == "summary":
            return self._build_summary_embed()

        records = await self._get_records(self.current_action)
        total_pages = max(1, math.ceil(len(records) / PAGE_SIZE)) if records else 1
        self.page = max(1, min(self.page, total_pages))

        embed = self.system.build_list_embed(
            member=self.member,
            records=records,
            action=self.system.normalize_action(self.current_action),
            include_inactive=self.include_inactive,
            page=self.page,
            per_page=PAGE_SIZE,
        )

        self._sync_pagination_buttons(records, total_pages)
        return embed

    async def handle_selection(self, interaction: discord.Interaction, action: str) -> None:
        self.current_action = action
        self.selector.update_default(action)
        self.page = 1
        embed = await self.build_embed()
        payload = embed

        if interaction.response.is_done():
            await interaction.edit_original_response(embed=payload, view=self)
        else:
            await interaction.response.edit_message(embed=payload, view=self)

    async def change_page(self, interaction: discord.Interaction, direction: int) -> None:
        if self.current_action == "summary":
            if not interaction.response.is_done():
                await interaction.response.defer()
            return

        records = await self._get_records(self.current_action)
        total_pages = max(1, math.ceil(len(records) / PAGE_SIZE)) if records else 1
        new_page = max(1, min(self.page + direction, total_pages))

        if new_page == self.page:
            if not interaction.response.is_done():
                await interaction.response.defer()
            return

        self.page = new_page
        embed = await self.build_embed()
        payload = embed

        if interaction.response.is_done():
            await interaction.edit_original_response(embed=payload, view=self)
        else:
            await interaction.response.edit_message(embed=payload, view=self)

    async def on_timeout(self) -> None:
        if hasattr(self, 'selector'):
            self.selector.disabled = True
        self.prev_button.disabled = True
        self.next_button.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass

    async def _get_records(self, action: str) -> list:
        if action not in self._records_cache:
            records = await self.system.fetch_records(
                member=self.member,
                action=action,
                include_inactive=self.include_inactive,
            )
            self._records_cache[action] = records
        return self._records_cache[action]

    def _sync_pagination_buttons(self, records: list, total_pages: int) -> None:
        if self.prev_button in self.children:
            self.remove_item(self.prev_button)
        if self.next_button in self.children:
            self.remove_item(self.next_button)

        if self.current_action == "warn" and len(records) > PAGE_SIZE:
            self.prev_button.disabled = self.page <= 1
            self.next_button.disabled = self.page >= total_pages
            self.add_item(self.prev_button)
            self.add_item(self.next_button)

    def _build_summary_embed(self) -> Embed:
        punishment_parts = []
        for ptype in ["ban", "mute", "warn"]:
            count = self.statistics.get(ptype, 0)
            if count > 0:
                label = PUNISHMENT_LABELS.get(ptype, ptype)
                if ptype == "ban":
                    word = "бан" if count == 1 else "бана" if 2 <= count <= 4 else "банов"
                elif ptype == "mute":
                    word = "мут" if count == 1 else "мута" if 2 <= count <= 4 else "мутов"
                else:
                    word = "варн" if count == 1 else "варна" if 2 <= count <= 4 else "варнов"
                punishment_parts.append(f"{count} {word}")

        if punishment_parts:
            description = DEFAULT_LOCALE.get("moderation", {}).get("rudiment_summary_some", "**Нарушения:** {list}").format(list=", ".join(punishment_parts))
        else:
            description = DEFAULT_LOCALE.get("moderation", {}).get("rudiment_summary_none", "**Нарушения:** отсутствуют")

        embed = Embed.default(
            title=f"{Emojis.MODERATION} {DEFAULT_LOCALE.get('moderation', {}).get('rudiment_summary_title', 'Нарушения пользователя')}",
            description=f"{self.member.mention}\n{description}",
        )
        embed.set_thumbnail(url=self.member.display_avatar.url)
        return embed

class Rudiments(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.system = RudimentsSystem(bot)

    @commands.hybrid_command(name="rudiments", description="Просмотреть нарушения пользователя по типам")
    @app_commands.describe(user="👤 Пользователь или ID для просмотра (по умолчанию — вы)")
    @moderationcommand(required_level=1, cooldown=5)
    async def rudiments(self, ctx: commands.Context, user: discord.Member = None) -> None:
        t = _(ctx=ctx)
        guild = ctx.guild
        if not guild:
            await ctx.send(embed=Embed.error(description=t("moderation", "rudiment_guild_only")))
            return

        target = user or ctx.author

        if not isinstance(target, discord.Member):
            await ctx.send(embed=Embed.error(description=t("moderation", "rudiment_user_not_found")))
            return

        statistics = {}
        for ptype in ["warn", "mute", "ban"]:
            records = await self.system.fetch_records(
                member=target,
                action=ptype,
                include_inactive=False,
            )
            statistics[ptype] = len(records)

        view = RudimentView(system=self.system, member=target, statistics=statistics)
        embed = await view.build_embed()
        payload = embed

        interaction = getattr(ctx, "interaction", None)
        if interaction:
            if interaction.response.is_done():
                view.message = await interaction.followup.send(embed=payload, view=view, ephemeral=True, wait=True)
            else:
                await interaction.response.send_message(embed=payload, view=view, ephemeral=True)
                view.message = await interaction.original_response()
        else:
            view.message = await ctx.send(embed=payload, view=view)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Rudiments(bot))

