from typing import Any, Dict, List, Optional
from ..tools.Embed import Embed
from ..tools.Emojis import Emojis
from ..tools.Time import TimeService
from ..locale import _

import discord

from Niludetsu.giveaways.conditions import GiveawayConditions

_time = TimeService()

class GiveawayConfigurator(discord.ui.View):

    def __init__(self, cog, guild: discord.Guild, author: discord.Member):
        super().__init__(timeout=900)
        self.cog = cog
        self.guild = guild
        self.author = author
        self._t = _(guild_id=guild.id, bot=cog.bot)

        self.config: Dict[str, Any] = {
            "channel_id": None,
            "prize": None,
            "winners": 1,
            "duration": "1h",
            "description": None,
            "mention_role_id": None,
            "settings": GiveawayConditions.defaults(),
        }

        self.message: Optional[discord.InteractionMessage] = None

        self.channel_select = _ChannelSelect(self)
        self.conditions_select = _ConditionsSelect(self)

        self.add_item(self.channel_select)
        self.add_item(self.conditions_select)

    @discord.ui.button(
        label="Настроить розыгрыш",
        style=discord.ButtonStyle.primary,
        emoji=Emojis.ICON_CONFIG,
    )
    async def setup_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        modal = GiveawayBaseModal(self.config, self._t)
        await interaction.response.send_modal(modal)
        await modal.wait()
        await self.refresh(interaction)

    @discord.ui.button(
        label="Создать", style=discord.ButtonStyle.success, emoji=Emojis.GIVEAWAY
    )
    async def create_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        t = self._t
        missing = []
        if not self.config["channel_id"]:
            missing.append(t("giveaways", "missing_channel"))
        if not self.config["prize"]:
            missing.append(t("giveaways", "missing_prize"))
        if missing:
            await interaction.response.send_message(
                t("giveaways", "missing_params", params=", ".join(missing)),
                ephemeral=True,
            )
            return

        channel = self.guild.get_channel(self.config["channel_id"])
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                t("giveaways", "channel_unavailable"), ephemeral=True
            )
            return

        try:
            await self.cog.manager.create_giveaway(
                channel=channel,
                host=self.author,
                prize=self.config["prize"],
                duration_input=self.config["duration"],
                winners=self.config["winners"],
                settings=self.config["settings"],
                mention_role_id=self.config["mention_role_id"],
            )
        except ValueError as err:
            await interaction.response.send_message(str(err), ephemeral=True)
            return

        await interaction.response.send_message(
            embed=Embed.success(
                title=f"🎉 {t('giveaways', 'created_title')}",
                description=t("giveaways", "created_desc", channel=channel.mention),
            ),
            ephemeral=True,
        )
        await self.close()

    @discord.ui.button(
        label="Отмена", style=discord.ButtonStyle.secondary, emoji=Emojis.ICON_IGNORE
    )
    async def cancel_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_message(
            self._t("giveaways", "creation_cancelled"), ephemeral=True
        )
        await self.close()

    def build_embed(self) -> discord.Embed:
        t = self._t
        embed = Embed.default(
            title=f"{Emojis.GIVEAWAY} {t('giveaways', 'config_title')}",
            description=t("giveaways", "config_desc"),
        )

        channel_value = (
            f"<#{self.config['channel_id']}>" if self.config["channel_id"] else "—"
        )
        embed.add_field(
            name=t("giveaways", "config_channel"), value=channel_value, inline=True
        )
        embed.add_field(
            name=t("giveaways", "config_prize"),
            value=self.config["prize"] or "—",
            inline=True,
        )
        embed.add_field(
            name=t("giveaways", "config_winners"),
            value=str(self.config["winners"]),
            inline=True,
        )

        seconds, human, error = _time.validate(
            self.config["duration"], max_days=30
        )
        embed.add_field(
            name=t("giveaways", "config_duration"),
            value=human if not error else f"⚠️ {error}",
            inline=True,
        )

        if self.config["mention_role_id"]:
            embed.add_field(
                name=t("giveaways", "config_mention"),
                value=f"<@&{self.config['mention_role_id']}>",
                inline=True,
            )

        description = self.config["description"] or t(
            "giveaways", "config_no_description"
        )
        embed.add_field(
            name=t("giveaways", "config_description"), value=description, inline=False
        )

        settings = self.config["settings"]
        conditions = []
        if settings["min_server_time"]:
            conditions.append(
                f"• {settings['min_server_time']} {t('giveaways', 'condition_days_on_server')}"
            )
        if settings["min_voice_time"]:
            conditions.append(
                f"• {settings['min_voice_time']} {t('giveaways', 'condition_minutes_in_voice')}"
            )
        if settings["required_role"]:
            conditions.append(
                f"• {t('giveaways', 'condition_role_prefix')} <@&{settings['required_role']}>"
            )
        if settings["min_level"]:
            conditions.append(
                f"• {t('giveaways', 'condition_min_level_prefix')} {settings['min_level']}"
            )
        if settings["booster_only"]:
            conditions.append(f"• {t('giveaways', 'condition_booster_only_text')}")
        if settings["no_revote"]:
            conditions.append(f"• {t('giveaways', 'condition_no_revote_text')}")
        embed.add_field(
            name=t("giveaways", "config_conditions"),
            value=(
                "\n".join(conditions)
                if conditions
                else t("giveaways", "config_no_conditions")
            ),
            inline=False,
        )

        return embed

    async def refresh(self, interaction: discord.Interaction):
        embed = self.build_embed()

        if self.message is None:
            try:
                self.message = await interaction.original_response()
            except discord.NotFound:
                pass

        if interaction.response.is_done():
            if self.message:
                try:
                    await interaction.followup.edit_message(
                        self.message.id, embed=embed, view=self
                    )
                except discord.HTTPException:
                    pass
        else:
            await interaction.response.edit_message(embed=embed, view=self)

    async def close(self):
        self.stop()
        if self.message:
            try:
                await self.message.edit(view=None)
            except discord.NotFound:
                pass

class GiveawayBaseModal(discord.ui.Modal, title="Параметры розыгрыша"):
    def __init__(self, config: Dict[str, Any], t=None):
        super().__init__(timeout=300)
        self.config = config
        self._t = t

        self.prize_input = discord.ui.TextInput(
            label=t("giveaways", "modal_prize_label") if t else "Приз",
            default=config["prize"] or "",
            max_length=100,
        )
        self.winners_input = discord.ui.TextInput(
            label=t("giveaways", "modal_winners_label") if t else "Количество победителей",
            default=str(config["winners"]),
            max_length=2,
        )
        self.duration_input = discord.ui.TextInput(
            label=t("giveaways", "modal_duration_label") if t else "Длительность (например: 1d, 12h, 30m)",
            default=config["duration"],
            max_length=10,
        )
        self.mention_input = discord.ui.TextInput(
            label=t("giveaways", "modal_mention_label") if t else "ID роли для упоминания (необязательно)",
            default=str(config["mention_role_id"] or ""),
            required=False,
        )
        self.description_input = discord.ui.TextInput(
            label=t("giveaways", "modal_desc_label") if t else "Описание (опционально)",
            default=config["description"] or "",
            required=False,
            style=discord.TextStyle.long,
            max_length=400,
        )

        for item in (
            self.prize_input,
            self.winners_input,
            self.duration_input,
            self.mention_input,
            self.description_input,
        ):
            self.add_item(item)

    async def on_submit(self, interaction: discord.Interaction):
        t = self._t or _(guild_id=interaction.guild_id, bot=interaction.client)
        try:
            winners = max(1, min(20, int(self.winners_input.value)))
        except ValueError:
            await interaction.response.send_message(
                t("giveaways", "winners_not_number"), ephemeral=True
            )
            return

        seconds, _, error = _time.validate(
            self.duration_input.value, max_days=30
        )
        if error:
            await interaction.response.send_message(error, ephemeral=True)
            return

        mention_raw = self.mention_input.value.strip()
        if mention_raw:
            if not mention_raw.isdigit():
                await interaction.response.send_message(
                    t("giveaways", "role_id_not_number"), ephemeral=True
                )
                return
            role = interaction.guild.get_role(int(mention_raw))
            if not role:
                await interaction.response.send_message(
                    t("giveaways", "role_not_found_id"), ephemeral=True
                )
                return
            self.config["mention_role_id"] = role.id
        else:
            self.config["mention_role_id"] = None

        self.config["prize"] = self.prize_input.value.strip() or None
        self.config["winners"] = winners
        self.config["duration"] = self.duration_input.value.strip()
        self.config["description"] = self.description_input.value.strip() or None

        await interaction.response.defer()

class ConditionValueModal(discord.ui.Modal):
    def __init__(self, title: str, unit: str, t=None):
        super().__init__(title=title, timeout=300)
        self.value: Optional[int] = None
        self._t = t
        self.input = discord.ui.TextInput(
            label=t("giveaways", "condition_value_label", unit=unit) if t else f"Введите число ({unit})",
            min_length=1,
            max_length=6,
        )
        self.add_item(self.input)

    async def on_submit(self, interaction: discord.Interaction):
        t = self._t or _(guild_id=interaction.guild_id, bot=interaction.client)
        try:
            val = int(self.input.value)
            if val < 0:
                raise ValueError
        except ValueError:
            await interaction.response.send_message(
                t("giveaways", "positive_number"), ephemeral=True
            )
            return
        self.value = val
        await interaction.response.defer()

class RoleModal(discord.ui.Modal, title="ID роли"):
    def __init__(self, t=None):
        super().__init__(timeout=300)
        self.role_id: Optional[int] = None
        self._t = t
        self.input = discord.ui.TextInput(
            label=t("giveaways", "role_modal_label") if t else "ID роли",
            min_length=1,
            max_length=20,
        )
        self.add_item(self.input)

    async def on_submit(self, interaction: discord.Interaction):
        t = self._t or _(guild_id=interaction.guild_id, bot=interaction.client)
        if not self.input.value.isdigit():
            await interaction.response.send_message(
                t("giveaways", "role_id_not_number"), ephemeral=True
            )
            return
        role = interaction.guild.get_role(int(self.input.value))
        if not role:
            await interaction.response.send_message(
                t("giveaways", "role_not_found_guild"), ephemeral=True
            )
            return
        self.role_id = role.id
        await interaction.response.defer()

class _ChannelSelect(discord.ui.Select):
    def __init__(self, configurator: GiveawayConfigurator):
        self.configurator = configurator
        t = configurator._t
        options = [
            discord.SelectOption(label=channel.name, value=str(channel.id))
            for channel in configurator.guild.text_channels[:25]
        ] or [
            discord.SelectOption(
                label=t("giveaways", "select_no_channels"),
                value="0",
                default=True,
            )
        ]

        super().__init__(
            placeholder=t("giveaways", "select_channel_placeholder"),
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "0":
            t = self.configurator._t
            await interaction.response.send_message(
                t("giveaways", "select_no_channels_available"), ephemeral=True
            )
            return
        self.configurator.config["channel_id"] = int(self.values[0])
        await self.configurator.refresh(interaction)

class _ConditionsSelect(discord.ui.Select):

    OPTIONS = {
        "min_server_time": ("min_server_time", "condition_unit_days"),
        "min_voice_time": ("min_voice_time", "condition_unit_minutes"),
        "required_role": ("required_role", None),
        "min_level": ("min_level", "condition_unit_level"),
        "booster_only": (None, None),
        "no_revote": (None, None),
    }

    def __init__(self, configurator: GiveawayConfigurator):
        self.configurator = configurator
        t = configurator._t
        super().__init__(
            placeholder=t("giveaways", "select_conditions_placeholder"),
            min_values=0,
            max_values=1,
            options=[
                discord.SelectOption(
                    label=t("giveaways", "condition_min_server_time"),
                    value="min_server_time",
                    emoji="⏱️",
                ),
                discord.SelectOption(
                    label=t("giveaways", "condition_min_voice_time"),
                    value="min_voice_time",
                    emoji="⏲️",
                ),
                discord.SelectOption(
                    label=t("giveaways", "condition_required_role"),
                    value="required_role",
                    emoji="🛡️",
                ),
                discord.SelectOption(
                    label=t("giveaways", "condition_min_level"),
                    value="min_level",
                    emoji="📊",
                ),
                discord.SelectOption(
                    label=t("giveaways", "condition_booster_only"),
                    value="booster_only",
                    emoji="🚀",
                ),
                discord.SelectOption(
                    label=t("giveaways", "condition_no_revote"),
                    value="no_revote",
                    emoji="🔄",
                ),
            ],
        )

    async def callback(self, interaction: discord.Interaction):
        if not self.values:
            return
        key = self.values[0]
        t = self.configurator._t
        settings = self.configurator.config["settings"]

        if key in {"booster_only", "no_revote"}:
            settings[key] = not settings.get(key, False)
            state = t("giveaways", "condition_enabled") if settings[key] else t("giveaways", "condition_disabled")
            await interaction.response.send_message(
                t("giveaways", "condition_toggled", label=self._label_by_key(key, t), state=state),
                ephemeral=True,
            )
            await self.configurator.refresh(interaction)
            return

        option_key, unit_key = self.OPTIONS[key]
        if key == "required_role":
            modal = RoleModal(t=t)
            await interaction.response.send_modal(modal)
            await modal.wait()
            if modal.role_id:
                settings["required_role"] = modal.role_id
        else:
            unit = t("giveaways", unit_key) if unit_key else ""
            label_key = f"condition_{option_key}" if not option_key.startswith("condition_") else option_key
            modal_title = t("giveaways", label_key) if t else key
            modal = ConditionValueModal(modal_title, unit, t=t)
            await interaction.response.send_modal(modal)
            await modal.wait()
            if modal.value is not None:
                settings[key] = modal.value

        if not interaction.response.is_done():
            await interaction.response.defer()
        await self.configurator.refresh(interaction)

    @staticmethod
    def _label_by_key(key: str, t=None) -> str:
        mapping = {
            "min_server_time": "condition_min_server_time",
            "min_voice_time": "condition_min_voice_time",
            "required_role": "condition_required_role",
            "min_level": "condition_min_level",
            "booster_only": "condition_booster_only",
            "no_revote": "condition_no_revote",
        }
        locale_key = mapping.get(key)
        if locale_key and t:
            return t("giveaways", locale_key)
        fallback = {
            "min_server_time": "Минимальное время на сервере",
            "min_voice_time": "Минимальное время в голосе",
            "required_role": "Необходимая роль",
            "min_level": "Минимальный уровень",
            "booster_only": "Только для бустеров",
            "no_revote": "Запрет на повторное участие",
        }
        return fallback.get(key, key)

class GiveawayParticipationView(discord.ui.View):

    def __init__(
        self,
        manager=None,
        giveaway_id: Optional[int] = None,
        participants_count: int = 0,
    ):
        super().__init__(timeout=None)
        self.manager = manager
        self.giveaway_id = giveaway_id
        self.count = participants_count

        join_id = (
            f"giveaway_join:{giveaway_id}" if giveaway_id else "giveaway_join:pending"
        )
        list_id = (
            f"giveaway_list:{giveaway_id}" if giveaway_id else "giveaway_list:pending"
        )

        self.join_button = discord.ui.Button(
            label=f"Участвовать ({self.count})",
            style=discord.ButtonStyle.primary,
            emoji="🎉",
            custom_id=join_id,
        )
        self.list_button = discord.ui.Button(
            label="Участники",
            style=discord.ButtonStyle.secondary,
            emoji="👥",
            custom_id=list_id,
        )

        self.join_button.callback = self.handle_join
        self.list_button.callback = self.handle_list

        self.add_item(self.join_button)
        self.add_item(self.list_button)

    async def ensure_manager(self, interaction: discord.Interaction):
        if self.manager:
            return
        cog = interaction.client.get_cog("Giveaways")
        if not cog:
            raise RuntimeError("Cog 'Giveaways' не найден.")
        self.manager = cog.manager

    async def ensure_giveaway_id(self, interaction: discord.Interaction):
        if self.giveaway_id:
            return
        custom_id = interaction.data.get("custom_id", "")
        if ":" in custom_id:
            _, value = custom_id.split(":", 1)
            if value.isdigit():
                self.giveaway_id = int(value)

    async def handle_join(self, interaction: discord.Interaction):
        await self.ensure_manager(interaction)
        await self.ensure_giveaway_id(interaction)
        t = _(guild_id=interaction.guild_id, bot=interaction.client)
        if not self.giveaway_id:
            await interaction.response.send_message(
                t("giveaways", "determine_giveaway_error"), ephemeral=True
            )
            return

        giveaway = await self.manager.get_giveaway(self.giveaway_id)
        if not giveaway or giveaway["is_ended"]:
            await interaction.response.send_message(
                t("giveaways", "giveaway_ended"), ephemeral=True
            )
            return

        guild = interaction.guild or interaction.client.get_guild(
            int(giveaway["guild_id"])
        )
        result = await GiveawayConditions.check(
            interaction.client,
            interaction.user,
            {"settings": giveaway.get("settings", {}), "host_id": giveaway["host_id"]},
            guild=guild,
        )
        if not result.get("success"):
            await interaction.response.send_message(
                f"{Emojis.GIVEAWAY} {t('giveaways', 'conditions_error')}\n- {result.get('reason', t('giveaways', 'conditions_reason_not_specified'))}",
                ephemeral=True,
            )
            return

        status = await self.manager.toggle_participation(
            self.giveaway_id, str(interaction.user.id)
        )
        if status == "inactive":
            await interaction.response.send_message(
                t("giveaways", "giveaway_inactive"), ephemeral=True
            )
            return

        participants = await self.manager.repo.list_participants(self.giveaway_id)
        self.count = len(participants)
        self.join_button.label = t("giveaways", "participate_button", count=self.count)

        message = (
            f"{Emojis.GIVEAWAY} {t('giveaways', 'participate_success')}"
            if status == "joined"
            else f"{Emojis.GIVEAWAY} {t('giveaways', 'participate_leave')}"
        )
        await interaction.response.send_message(message, ephemeral=True)
        if interaction.message:
            await interaction.message.edit(view=self)

    async def handle_list(self, interaction: discord.Interaction):
        await self.ensure_manager(interaction)
        await self.ensure_giveaway_id(interaction)
        t = _(guild_id=interaction.guild_id, bot=interaction.client)
        if not self.giveaway_id:
            await interaction.response.send_message(
                t("giveaways", "determine_giveaway_error"), ephemeral=True
            )
            return

        giveaway = await self.manager.get_giveaway(self.giveaway_id)
        if not giveaway:
            await interaction.response.send_message(
                t("giveaways", "giveaway_not_found"), ephemeral=True
            )
            return

        participants = await self.manager.repo.list_participants(self.giveaway_id)
        winners_count = giveaway.get("winners_count", 1)
        if not participants:
            await interaction.response.send_message(
                f"{Emojis.GIVEAWAY} {t('giveaways', 'no_participants')}",
                ephemeral=True,
            )
            return

        chance = (winners_count / len(participants)) * 100
        lines: List[str] = []
        for user_id in participants:
            member = (
                interaction.guild.get_member(int(user_id))
                if interaction.guild
                else None
            )
            if member:
                lines.append(f"{member.mention} — **{chance:.1f}%**")
            else:
                try:
                    user = await interaction.client.fetch_user(int(user_id))
                    lines.append(
                        f"{discord.utils.escape_markdown(user.name)} — **{chance:.1f}%**"
                    )
                except Exception:
                    lines.append(f"<@{user_id}> — **{chance:.1f}%**")

        per_page = 15
        pages = [lines[i : i + per_page] for i in range(0, len(lines), per_page)]

        def make_embed(page_idx: int) -> Embed:
            page_lines = pages[page_idx]
            footer = t("giveaways", "participants_page", page=page_idx + 1, total=len(pages)) if len(pages) > 1 else ""
            embed = Embed(
                title=f"{Emojis.GIVEAWAY} {t('giveaways', 'participants_title')}",
                description=(
                    f"{t('giveaways', 'participants_total', count=len(participants))}\n"
                    f"{t('giveaways', 'participants_prize_places', count=winners_count)}\n"
                    + "\n".join(page_lines)
                ),
                color=Colors.SUCCESS,
            )
            if footer:
                embed.set_footer(text=footer)
            return embed

        if len(pages) == 1:
            await interaction.response.send_message(embed=make_embed(0), ephemeral=True)
            return

        class Paginator(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=120)
                self.page = 0
                self.prev_btn = discord.ui.Button(
                    emoji=Emojis.ICON_ARROW_LEFT, style=discord.ButtonStyle.secondary
                )
                self.next_btn = discord.ui.Button(
                    emoji=Emojis.ICON_ARROW_RIGHT, style=discord.ButtonStyle.secondary
                )
                self.prev_btn.callback = self.prev
                self.next_btn.callback = self.next
                self.add_item(self.prev_btn)
                self.add_item(self.next_btn)

            async def prev(self, btn_inter: discord.Interaction):
                if btn_inter.user.id != interaction.user.id:
                    await btn_inter.response.defer()
                    return
                self.page = (self.page - 1) % len(pages)
                await btn_inter.response.edit_message(
                    embed=make_embed(self.page), view=self
                )

            async def next(self, btn_inter: discord.Interaction):
                if btn_inter.user.id != interaction.user.id:
                    await btn_inter.response.defer()
                    return
                self.page = (self.page + 1) % len(pages)
                await btn_inter.response.edit_message(
                    embed=make_embed(self.page), view=self
                )

        await interaction.response.send_message(
            embed=make_embed(0),
            view=Paginator(),
            ephemeral=True,
        )
