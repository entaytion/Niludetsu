import discord
from discord import app_commands, Interaction
from discord.ext import commands
from discord.ui import Button, Select, View
from Niludetsu import Embed, Time, config, Emojis, resolve_member, safe_fetch_user
from Niludetsu.database import database
from Niludetsu.locale import _, DEFAULT_LOCALE
from typing import Dict, List, Optional

MAIN_GUILD_ID = str(config.SERVERS["MAIN_ID"])
_time = Time()
P = DEFAULT_LOCALE.get("profile", {})

class LeaderboardView(View):
    def __init__(self, cog: "Leaderboard", interaction: Interaction, t, category: str = "level") -> None:
        super().__init__(timeout=90)
        self.cog = cog
        self.interaction = interaction
        self.t = t
        self.category = category
        self.current_page = 1
        self.per_page = 10
        self.entries: List[Dict] = []
        self.category_title = ""
        self.rank_map: Dict[str, int] = {}
        self.rank_enabled = True
        self._display_cache: Dict[int, str] = {}

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user.id != self.interaction.user.id:
            await interaction.response.send_message(
                P.get("leaderboard_not_for_you", "Эта панель — для того, кто её вызвал."),
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True
        try:
            await self.interaction.edit_original_response(view=self)
        except discord.Forbidden:
            pass

    async def initialize(self, category: str) -> bool:
        self.category = category
        for child in self.children:
            if isinstance(child, Select):
                child.placeholder = self.t("profile", "leaderboard_select")
        await self.load_entries()
        await self.update_buttons()
        return bool(self.entries)

    async def load_entries(self) -> None:
        if self.category == "level":
            await self._load_levels()
        elif self.category == "economy":
            await self._load_economy()
        elif self.category == "messages":
            await self._load_messages()
        elif self.category == "voice":
            await self._load_voice()
        elif self.category == "families":
            await self._load_families()
        elif self.category == "reputation":
            await self._load_reputation()
        else:
            self.entries = []
            self.category_title = self.t("profile", "leaderboard_unknown")

        if self.rank_enabled:
            self.rank_map = {entry["key"]: index for index, entry in enumerate(self.entries, start=1)}
        else:
            self.rank_map = {}

    async def _fetch_all_rows(
        self,
        table: str,
        *,
        columns: Optional[List[str]] = None,
        filters: Optional[List[Dict]] = None,
        order: Optional[List[Dict]] = None,
        chunk_size: int = 1000,
    ) -> List[Dict]:
        rows: List[Dict] = []
        offset = 0
        while True:
            batch = await database.where(
                table,
                columns=columns,
                filters=filters,
                order=order,
                limit=chunk_size,
                offset=offset,
            )
            rows.extend(batch)
            if len(batch) < chunk_size:
                break
            offset += chunk_size
        return rows

    async def _load_levels(self) -> None:
        rows = await self._fetch_all_rows(
            "user_profile",
            columns=["user_id", "level", "experience"],
            filters=[{"column": "guild_id", "value": MAIN_GUILD_ID}],
        )

        filtered = [
            row for row in rows
            if (row.get("level", 1) > 1) or (row.get("experience", 0) > 0)
        ]
        filtered.sort(
            key=lambda row: (int(row.get("level", 1)), int(row.get("experience", 0))),
            reverse=True,
        )

        e_t = self.t
        entries = [
            {
                "key": str(row["user_id"]),
                "value": e_t("profile", "leaderboard_entry_level", level=row.get('level', 1), xp=row.get('experience', 0)),
            }
            for row in filtered
        ]

        self.entries = entries
        self.category_title = self.t("profile", "leaderboard_cat_level_title")
        self.rank_enabled = True

    async def _load_economy(self) -> None:
        rows = await self._fetch_all_rows(
            "user_economy",
            columns=["user_id", "balance", "deposit", "spousal_balance"],
            filters=[{"column": "guild_id", "value": MAIN_GUILD_ID}],
        )

        entries = []
        for row in rows:
            total = sum(
                value for value in [
                    row.get("balance"),
                    row.get("deposit"),
                    row.get("spousal_balance"),
                ]
                if isinstance(value, (int, float))
            )
            if total <= 0:
                continue

            balance = max(int(row.get("balance", 0)), 0)
            deposit = max(int(row.get("deposit", 0)), 0)
            spousal = max(int(row.get("spousal_balance") or 0), 0)

            user_id = str(row["user_id"])
            entries.append(
                {
                    "key": user_id,
                    "value": self.t("profile", "leaderboard_entry_economy", total=total, balance=balance, deposit=deposit, spousal=spousal),
                    "total": total,
                }
            )

        entries.sort(key=lambda entry: entry["total"], reverse=True)
        for entry in entries:
            entry.pop("total", None)

        self.entries = entries
        self.category_title = self.t("profile", "leaderboard_cat_economy_title")
        self.rank_enabled = True

    async def _load_messages(self) -> None:
        rows = await self._fetch_all_rows(
            "user_analytics",
            columns=["user_id", "messages_total"],
            filters=[{"column": "guild_id", "value": MAIN_GUILD_ID}],
        )

        entries = []
        for row in rows:
            total = int(row.get("messages_total") or 0)
            if total <= 0:
                continue
            user_id = str(row["user_id"])
            entries.append(
                {
                    "key": user_id,
                    "value": self.t("profile", "leaderboard_entry_messages", total=total),
                    "total": total,
                }
            )

        entries.sort(key=lambda entry: entry["total"], reverse=True)
        for entry in entries:
            entry.pop("total", None)

        self.entries = entries
        self.category_title = self.t("profile", "leaderboard_cat_messages_title")
        self.rank_enabled = True

    async def _load_voice(self) -> None:
        rows = await self._fetch_all_rows(
            "user_analytics",
            columns=["user_id", "voice_seconds"],
            filters=[{"column": "guild_id", "value": MAIN_GUILD_ID}],
        )

        entries = []
        for row in rows:
            seconds = int(row.get("voice_seconds") or 0)
            if seconds <= 0:
                continue

            user_id = str(row["user_id"])
            entries.append(
                {
                    "key": user_id,
                    "value": self.t("profile", "leaderboard_entry_voice", duration=_time.format_duration(seconds)),
                    "total": seconds,
                }
            )

        entries.sort(key=lambda entry: entry["total"], reverse=True)
        for entry in entries:
            entry.pop("total", None)

        self.entries = entries
        self.category_title = self.t("profile", "leaderboard_cat_voice_title")
        self.rank_enabled = True

    async def _load_families(self) -> None:
        rows = await self._fetch_all_rows(
            "user_marriages",
            columns=["partner_a_id", "partner_b_id", "married_at"],
            filters=[
                {"column": "guild_id", "value": MAIN_GUILD_ID},
                {"column": "status", "value": "active"},
            ],
        )

        entries = []
        now = _time.now()

        for row in rows:
            married_at = _time.ensure_datetime(row.get("married_at"))
            if not married_at:
                continue

            duration_seconds = max(int((now - married_at).total_seconds()), 0)
            partner_a = int(row.get("partner_a_id"))
            partner_b = int(row.get("partner_b_id"))

            entries.append(
                {
                    "key": f"{partner_a}:{partner_b}",
                    "partners": [partner_a, partner_b],
                    "value": self.t("profile", "leaderboard_entry_families", duration=_time.format_duration(duration_seconds)),
                    "total": duration_seconds,
                }
            )

        entries.sort(key=lambda entry: entry["total"], reverse=True)
        for entry in entries:
            entry.pop("total", None)

        self.entries = entries
        self.category_title = self.t("profile", "leaderboard_cat_families_title")
        self.rank_enabled = False

    async def _load_reputation(self) -> None:
        rows = await self._fetch_all_rows(
            "user_profile",
            columns=["user_id", "reputation"],
            filters=[{"column": "guild_id", "value": MAIN_GUILD_ID}],
        )

        entries = []
        for row in rows:
            rep = int(row.get("reputation") or 0)
            if rep <= 0:
                continue

            user_id = str(row["user_id"])
            entries.append(
                {
                    "key": user_id,
                    "value": self.t("profile", "leaderboard_entry_reputation", rep=rep),
                    "total": rep,
                }
            )

        entries.sort(key=lambda entry: entry["total"], reverse=True)
        for entry in entries:
            entry.pop("total", None)

        self.entries = entries
        self.category_title = self.t("profile", "leaderboard_cat_reputation_title")
        self.rank_enabled = True

    async def update_buttons(self) -> None:
        total_pages = self.total_pages
        self.first_page_button.disabled = self.current_page <= 1
        self.prev_page_button.disabled = self.current_page <= 1
        self.next_page_button.disabled = self.current_page >= total_pages
        self.last_page_button.disabled = self.current_page >= total_pages

    @property
    def total_pages(self) -> int:
        if not self.entries:
            return 1
        return (len(self.entries) + self.per_page - 1) // self.per_page

    async def update_message(self, interaction: Interaction) -> None:
        await self.update_buttons()
        embed = await self.create_embed()
        try:
            if interaction.response.is_done():
                await interaction.edit_original_response(embed=embed, view=self)
            else:
                await interaction.response.edit_message(embed=embed, view=self)
        except Exception:
            try:
                if hasattr(self, "message") and self.message:
                    await self.message.edit(embed=embed, view=self)
            except Exception:
                pass

    async def create_embed(self) -> Embed:
        embed = Embed(
            title=self.t("profile", "leaderboard_title", category=self.category_title),
            description=f"{Emojis.UNKNOWN} {self.t('profile', 'leaderboard_page', page=self.current_page, total=self.total_pages)}",
        )

        start = (self.current_page - 1) * self.per_page
        end = start + self.per_page
        page_entries = self.entries[start:end]

        if not page_entries:
            embed.description = f"{Emojis.UNKNOWN} {self.t('profile', 'leaderboard_empty')}"
            return embed

        if self.rank_enabled:
            user_key = str(self.interaction.user.id)
            if user_key in self.rank_map:
                embed.set_footer(
                    text=self.t("profile", "leaderboard_your_rank", rank=self.rank_map[user_key]),
                    icon_url=self.interaction.user.display_avatar.url,
                )
            else:
                embed.set_footer(
                    text=self.t("profile", "leaderboard_not_ranked"),
                    icon_url=self.interaction.user.display_avatar.url,
                )
        else:
            embed.set_footer(text=self.t("profile", "leaderboard_love_footer"))

        for index, entry in enumerate(page_entries, start=start + 1):
            title = await self._resolve_entry_title(entry)
            embed.add_field(
                name=f"#{index}. {title}",
                value=entry["value"],
                inline=False,
            )

        return embed

    async def _resolve_entry_title(self, entry: Dict) -> str:
        if "partners" in entry:
            partner_ids = entry["partners"]
            names = [await self._get_display_name(pid) for pid in partner_ids]
            return self.t("profile", "leaderboard_entry_family_names", name1=names[0], name2=names[1])
        user_id = int(entry["key"])
        return await self._get_display_name(user_id)

    @discord.ui.button(emoji=Emojis.ICON_DOUBLE_ARROW_LEFT, style=discord.ButtonStyle.gray, row=1)
    async def first_page_button(self, interaction: Interaction, _: Button) -> None:
        if not interaction.response.is_done():
            await interaction.response.defer()
        if self.current_page != 1:
            self.current_page = 1
        await self.update_message(interaction)

    @discord.ui.button(emoji=Emojis.ICON_ARROW_LEFT, style=discord.ButtonStyle.gray, row=1)
    async def prev_page_button(self, interaction: Interaction, _: Button) -> None:
        if not interaction.response.is_done():
            await interaction.response.defer()
        if self.current_page > 1:
            self.current_page -= 1
        await self.update_message(interaction)

    @discord.ui.button(emoji=Emojis.ICON_ARROW_RIGHT, style=discord.ButtonStyle.gray, row=1)
    async def next_page_button(self, interaction: Interaction, _: Button) -> None:
        if not interaction.response.is_done():
            await interaction.response.defer()
        if self.current_page < self.total_pages:
            self.current_page += 1
        await self.update_message(interaction)

    @discord.ui.button(emoji=Emojis.ICON_DOUBLE_ARROW_RIGHT, style=discord.ButtonStyle.gray, row=1)
    async def last_page_button(self, interaction: Interaction, _: Button) -> None:
        if not interaction.response.is_done():
            await interaction.response.defer()
        if self.current_page != self.total_pages:
            self.current_page = self.total_pages
        await self.update_message(interaction)

    @discord.ui.select(
        placeholder=P.get("leaderboard_select", "Выбери категорию"),
        options=[
            discord.SelectOption(label=P.get("leaderboard_cat_level", "Уровни"), value="level", emoji=Emojis.ICON_STATISTICS),
            discord.SelectOption(label=P.get("leaderboard_cat_economy", "Капитал"), value="economy", emoji=Emojis.ICON_MONEY),
            discord.SelectOption(label=P.get("leaderboard_cat_messages", "Сообщения"), value="messages", emoji=Emojis.ICON_CHAT),
            discord.SelectOption(label=P.get("leaderboard_cat_voice", "Голосовые"), value="voice", emoji=Emojis.ICON_VOICE),
            discord.SelectOption(label=P.get("leaderboard_cat_families", "Долголетние семьи"), value="families", emoji="💍"),
            discord.SelectOption(label=P.get("leaderboard_cat_reputation", "Репутация"), value="reputation", emoji="⭐"),
        ],
        row=0,
    )
    async def category_select(self, interaction: Interaction, select: Select) -> None:
        if not interaction.response.is_done():
            await interaction.response.defer()
        self.current_page = 1
        self.category = select.values[0]
        await self.load_entries()

        if not self.entries:
            await interaction.followup.send(
                embed=Embed.warn(
                    title=self.t("profile", "leaderboard_empty_category_title"),
                    description=self.t("profile", "leaderboard_empty_category"),
                ),
                ephemeral=True,
            )
            return

        await self.update_message(interaction)

class Leaderboard(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def get_member_display(self, user_id: int) -> str:
        member = await resolve_member(self.bot, user_id, MAIN_GUILD_ID)
        return getattr(member, "display_name", getattr(member, "name", P.get("leaderboard_user_fallback", "Пользователь #{user_id}").format(user_id=user_id)))

    @app_commands.command(name="leaderboard", description="Показать топы сервера")
    async def leaderboard(self, interaction: Interaction) -> None:
        await interaction.response.defer()
        t = _(guild_id=interaction.guild_id, bot=self.bot)
        view = LeaderboardView(self, interaction, t)
        await view.initialize("level")
        embed = await view.create_embed()
        await interaction.followup.send(embed=embed, view=view)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Leaderboard(bot))
