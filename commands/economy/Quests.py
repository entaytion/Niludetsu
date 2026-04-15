import discord
from discord import app_commands
from discord.ext import commands
from Niludetsu import Emojis
from Niludetsu.database.supabase_database import database
from Niludetsu.quests.definitions import total_pages
from Niludetsu.quests.manager import QuestManager, QuestProgress
from Niludetsu.tools.Embed import Embed, Colors
from Niludetsu.tools.Time import TimeService
from typing import List, Optional

_time = TimeService()


class QuestClaimSelect(discord.ui.Select):
    """Select menu для получения награды за квест."""

    def __init__(self, quest_manager: QuestManager, claimable: List[QuestProgress], user_id: str, guild_id: str):
        self.quest_manager = quest_manager
        self._user_id = user_id
        self._guild_id = guild_id

        if not claimable:
            options = [discord.SelectOption(label="—", value="_none_")]
            super().__init__(
                placeholder="Нет квестов для получения награды",
                options=options,
                disabled=True,
                min_values=1, max_values=1,
            )
        else:
            options = []
            for qp in claimable:
                options.append(discord.SelectOption(
                    label=f"{qp.quest['name']} — {qp.quest['reward']:,} монет",
                    value=qp.quest["key"],
                    description=qp.quest["description"][:100],
                ))
            super().__init__(
                placeholder="Выберите квест для получения награды",
                options=options,
                min_values=1, max_values=1,
            )

    async def callback(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self._user_id:
            await interaction.response.send_message(
                embed=Embed.error(description="Эта менюшка не для тебя."),
                ephemeral=True,
            )
            return

        quest_key = self.values[0]
        if quest_key == "_none_":
            await interaction.response.defer()
            return

        success, message = await self.quest_manager.claim_reward(
            self._user_id, self._guild_id, quest_key,
        )

        if success:
            embed = Embed.success(description=f"{interaction.user.mention}, {message}")
        else:
            embed = Embed.error(description=message)

        await interaction.response.send_message(embed=embed, ephemeral=True)

        # Обновляем оригинальное сообщение
        view: QuestsView = self.view
        await view.refresh(interaction)


class QuestsView(discord.ui.View):
    """View с пагинацией и select menu."""

    def __init__(
        self,
        quest_manager: QuestManager,
        user: discord.Member | discord.User,
        guild_id: str,
        page: int = 1,
    ):
        super().__init__(timeout=120)
        self.quest_manager = quest_manager
        self.user = user
        self.guild_id = guild_id
        self.page = page
        self.max_pages = total_pages()
        self.message: Optional[discord.Message] = None

    async def build(self) -> tuple[Embed, "QuestsView"]:
        """Строит embed + обновляет компоненты."""
        user_id = str(self.user.id)
        guild_id = self.guild_id

        # Получаем прогресс квестов на текущей странице
        quests = await self.quest_manager.get_user_quests(user_id, guild_id, self.page)
        claimable = await self.quest_manager.get_claimable_quests(user_id, guild_id)

        # Строим embed
        embed = self._build_embed(quests)

        # Чистим и ставим новые компоненты
        self.clear_items()
        self.add_item(QuestClaimSelect(self.quest_manager, claimable, user_id, guild_id))
        self._add_buttons()

        return embed, self

    def _build_embed(self, quests: List[QuestProgress]) -> Embed:
        lines = []
        for qp in quests:
            q = qp.quest

            # Статус
            if qp.reward_claimed:
                status = "✅ Получена"
            elif qp.completed:
                status = "🎉 Завершён"
            else:
                status = "⏳ Выполняется"

            # Прогресс
            progress = min(qp.progress, q["goal"])

            # Время до сброса
            reset_text = "—"
            if qp.resets_at:
                reset_dt = _time.ensure_datetime(qp.resets_at)
                if reset_dt:
                    now = _time.now()
                    diff = int((reset_dt - now).total_seconds())
                    if diff > 0:
                        reset_text = _time.format_duration(diff)
                    else:
                        reset_text = "скоро"

            lines.append(
                f"**{q['name']}**\n"
                f"{q['description']}\n"
                f"> Статус: **{status}**\n"
                f"> Цель: **{progress}/{q['goal']}**\n"
                f"> Награда: **{q['reward']:,}** {Emojis.MONEY}\n"
                f"> Сброс через: **{reset_text}**"
            )

        description = "\n\n".join(lines) if lines else "Квестов нет."

        page_label = "Ежедневные" if self.page == 1 else "Еженедельные"

        return Embed.user(
            user=self.user,
            title_prefix="Квесты",
            description=f"**{page_label} квесты**\n\n{description}",
            color=Colors.PRIMARY,
            footer={"text": f"Страница {self.page}/{self.max_pages}"},
        )

    def _add_buttons(self):
        # Предыдущая
        prev_btn = discord.ui.Button(
            label="Предыдущая",
            style=discord.ButtonStyle.secondary,
            custom_id="quests_previous",
            disabled=self.page <= 1,
        )
        prev_btn.callback = self._prev
        self.add_item(prev_btn)

        # Следующая
        next_btn = discord.ui.Button(
            label="Следующая",
            style=discord.ButtonStyle.secondary,
            custom_id="quests_next",
            disabled=self.page >= self.max_pages,
        )
        next_btn.callback = self._next
        self.add_item(next_btn)

    async def _prev(self, interaction: discord.Interaction):
        if str(interaction.user.id) != str(self.user.id):
            await interaction.response.send_message(
                embed=Embed.error(description="Не твои квесты."), ephemeral=True,
            )
            return
        self.page = max(1, self.page - 1)
        await self.refresh(interaction)

    async def _next(self, interaction: discord.Interaction):
        if str(interaction.user.id) != str(self.user.id):
            await interaction.response.send_message(
                embed=Embed.error(description="Не твои квесты."), ephemeral=True,
            )
            return
        self.page = min(self.max_pages, self.page + 1)
        await self.refresh(interaction)

    async def refresh(self, interaction: discord.Interaction):
        embed, _ = await self.build()
        if interaction.response.is_done():
            await interaction.message.edit(embed=embed, view=self)
        else:
            await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self):
        if self.message:
            try:
                await self.message.edit(view=None)
            except Exception:
                pass


class Quests(commands.Cog):
    """Команда квестов."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = database
        self.quest_manager = QuestManager(self.db)

    @commands.hybrid_command(
        name="quests",
        aliases=("квесты", "quest"),
        description="📋 Посмотреть доступные квесты и прогресс",
    )
    @app_commands.describe()
    async def quests(self, ctx: commands.Context) -> None:
        if ctx.interaction and not ctx.interaction.response.is_done():
            await ctx.defer()

        user = ctx.author
        guild_id = str(ctx.guild.id)

        view = QuestsView(
            quest_manager=self.quest_manager,
            user=user,
            guild_id=guild_id,
            page=1,
        )

        embed, view = await view.build()
        msg = await ctx.reply(embed=embed, view=view, mention_author=False)
        view.message = msg


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Quests(bot))
