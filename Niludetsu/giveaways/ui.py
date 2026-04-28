from typing import Any, Dict, Optional
from ..tools.Embed import Embed
from ..tools.Emojis import Emojis
from ..tools.Time import TimeService

import discord

from Niludetsu.giveaways.conditions import GiveawayConditions

_time = TimeService()

class GiveawayConfigurator(discord.ui.View):
    """Единый мастер создания розыгрыша."""

    def __init__(self, cog, guild: discord.Guild, author: discord.Member):
        super().__init__(timeout=900)
        self.cog = cog
        self.guild = guild
        self.author = author

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

    # Кнопки
    @discord.ui.button(
        label="Настроить розыгрыш",
        style=discord.ButtonStyle.primary,
        emoji=Emojis.ICON_CONFIG,
    )
    async def setup_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        modal = GiveawayBaseModal(self.config)
        await interaction.response.send_modal(modal)
        await modal.wait()
        await self.refresh(interaction)

    @discord.ui.button(
        label="Создать", style=discord.ButtonStyle.success, emoji=Emojis.GIVEAWAY
    )
    async def create_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        missing = []
        if not self.config["channel_id"]:
            missing.append("канал")
        if not self.config["prize"]:
            missing.append("приз")
        if missing:
            await interaction.response.send_message(
                f"Не хватает параметров: {', '.join(missing)}.",
                ephemeral=True,
            )
            return

        channel = self.guild.get_channel(self.config["channel_id"])
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                "Выбранный канал недоступен.", ephemeral=True
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
                title="🎉 Розыгрыш создан!",
                description=f"Сообщение отправлено в {channel.mention}.",
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
        await interaction.response.send_message("Создание отменено.", ephemeral=True)
        await self.close()

    # Служебные методы
    def build_embed(self) -> discord.Embed:
        embed = Embed.default(
            title=f"{Emojis.GIVEAWAY} Настройка розыгрыша",
            description="Заполните параметры и посмотрите предпросмотр.",
        )

        channel_value = (
            f"<#{self.config['channel_id']}>" if self.config["channel_id"] else "—"
        )
        embed.add_field(name="Канал", value=channel_value, inline=True)
        embed.add_field(name="Приз", value=self.config["prize"] or "—", inline=True)
        embed.add_field(
            name="Победители", value=str(self.config["winners"]), inline=True
        )

        seconds, human, error = _time.validate(
            self.config["duration"], max_days=30
        )
        embed.add_field(
            name="Длительность",
            value=human if not error else f"⚠️ {error}",
            inline=True,
        )

        if self.config["mention_role_id"]:
            embed.add_field(
                name="Уведомление",
                value=f"<@&{self.config['mention_role_id']}>",
                inline=True,
            )

        description = self.config["description"] or "— описание не указано —"
        embed.add_field(name="Описание", value=description, inline=False)

        settings = self.config["settings"]
        conditions = []
        if settings["min_server_time"]:
            conditions.append(f"• {settings['min_server_time']} дн. на сервере")
        if settings["min_voice_time"]:
            conditions.append(f"• {settings['min_voice_time']} мин. в голосе")
        if settings["required_role"]:
            conditions.append(f"• Роль: <@&{settings['required_role']}>")
        if settings["min_level"]:
            conditions.append(f"• Минимальный уровень: {settings['min_level']}")
        if settings["booster_only"]:
            conditions.append("• Только для бустеров")
        if settings["no_revote"]:
            conditions.append("• Повторное участие запрещено")
        embed.add_field(
            name="Условия",
            value="\n".join(conditions) if conditions else "— условия отсутствуют —",
            inline=False,
        )

        return embed

    async def refresh(self, interaction: discord.Interaction):
        """Обновляет предпросмотр после изменения параметров."""
        embed = self.build_embed()

        if self.message is None:
            # Если ещё нет исходного сообщения, попытаться получить его
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

# Модалки
class GiveawayBaseModal(discord.ui.Modal, title="Параметры розыгрыша"):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(timeout=300)
        self.config = config

        self.prize_input = discord.ui.TextInput(
            label="Приз",
            default=config["prize"] or "",
            max_length=100,
        )
        self.winners_input = discord.ui.TextInput(
            label="Количество победителей",
            default=str(config["winners"]),
            max_length=2,
        )
        self.duration_input = discord.ui.TextInput(
            label="Длительность (например: 1d, 12h, 30m)",
            default=config["duration"],
            max_length=10,
        )
        self.mention_input = discord.ui.TextInput(
            label="ID роли для упоминания (необязательно)",
            default=str(config["mention_role_id"] or ""),
            required=False,
        )
        self.description_input = discord.ui.TextInput(
            label="Описание (опционально)",
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
        try:
            winners = max(1, min(20, int(self.winners_input.value)))
        except ValueError:
            await interaction.response.send_message(
                "Количество победителей должно быть числом.", ephemeral=True
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
                    "ID роли должен быть числом.", ephemeral=True
                )
                return
            role = interaction.guild.get_role(int(mention_raw))
            if not role:
                await interaction.response.send_message(
                    "Роль с таким ID не найдена.", ephemeral=True
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
    def __init__(self, title: str, unit: str):
        super().__init__(title=title, timeout=300)
        self.value: Optional[int] = None
        self.input = discord.ui.TextInput(
            label=f"Введите число ({unit})",
            min_length=1,
            max_length=6,
        )
        self.add_item(self.input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            val = int(self.input.value)
            if val < 0:
                raise ValueError
        except ValueError:
            await interaction.response.send_message(
                "Нужно положительное число.", ephemeral=True
            )
            return
        self.value = val
        await interaction.response.defer()

class RoleModal(discord.ui.Modal, title="ID роли"):
    def __init__(self):
        super().__init__(timeout=300)
        self.role_id: Optional[int] = None
        self.input = discord.ui.TextInput(label="ID роли", min_length=1, max_length=20)
        self.add_item(self.input)

    async def on_submit(self, interaction: discord.Interaction):
        if not self.input.value.isdigit():
            await interaction.response.send_message(
                "ID роли должен быть числом.", ephemeral=True
            )
            return
        role = interaction.guild.get_role(int(self.input.value))
        if not role:
            await interaction.response.send_message(
                "Роль не найдена на сервере.", ephemeral=True
            )
            return
        self.role_id = role.id
        await interaction.response.defer()

# Селекты
class _ChannelSelect(discord.ui.Select):
    def __init__(self, configurator: GiveawayConfigurator):
        self.configurator = configurator
        options = [
            discord.SelectOption(label=channel.name, value=str(channel.id))
            for channel in configurator.guild.text_channels[:25]
        ] or [
            discord.SelectOption(
                label="Текстовые каналы отсутствуют",
                value="0",
                default=True,
            )
        ]

        super().__init__(
            placeholder="Выберите канал для розыгрыша",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "0":
            await interaction.response.send_message(
                "Нет доступных текстовых каналов.", ephemeral=True
            )
            return
        self.configurator.config["channel_id"] = int(self.values[0])
        await self.configurator.refresh(interaction)

class _ConditionsSelect(discord.ui.Select):
    """Выпадающий список условий. За раз — одно условие, чтобы не путать модалки."""

    OPTIONS = {
        "min_server_time": ("Мин. время на сервере", "дни"),
        "min_voice_time": ("Мин. время в голосе", "минуты"),
        "required_role": ("Необходимая роль", None),
        "min_level": ("Минимальный уровень", "уровень"),
        "booster_only": (None, None),
        "no_revote": (None, None),
    }

    def __init__(self, configurator: GiveawayConfigurator):
        self.configurator = configurator
        super().__init__(
            placeholder="Добавить/изменить условие",
            min_values=0,
            max_values=1,
            options=[
                discord.SelectOption(
                    label="Мин. время на сервере", value="min_server_time", emoji="⏱️"
                ),
                discord.SelectOption(
                    label="Мин. время в голосе", value="min_voice_time", emoji="⏲️"
                ),
                discord.SelectOption(
                    label="Необходимая роль", value="required_role", emoji="🛡️"
                ),
                discord.SelectOption(
                    label="Мин. уровень", value="min_level", emoji="📊"
                ),
                discord.SelectOption(
                    label="Только для бустеров", value="booster_only", emoji="🚀"
                ),
                discord.SelectOption(
                    label="Запрет на повторное участие", value="no_revote", emoji="🔄"
                ),
            ],
        )

    async def callback(self, interaction: discord.Interaction):
        if not self.values:
            return
        key = self.values[0]
        settings = self.configurator.config["settings"]

        if key in {"booster_only", "no_revote"}:
            settings[key] = not settings.get(key, False)
            state = "включено" if settings[key] else "отключено"
            await interaction.response.send_message(
                f"Условие «{self._label_by_key(key)}» {state}.", ephemeral=True
            )
            await self.configurator.refresh(interaction)
            return

        title, unit = self.OPTIONS[key]
        if key == "required_role":
            modal = RoleModal()
            await interaction.response.send_modal(modal)
            await modal.wait()
            if modal.role_id:
                settings["required_role"] = modal.role_id
        else:
            modal = ConditionValueModal(title, unit)
            await interaction.response.send_modal(modal)
            await modal.wait()
            if modal.value is not None:
                settings[key] = modal.value

        if not interaction.response.is_done():
            await interaction.response.defer()
        await self.configurator.refresh(interaction)

    @staticmethod
    def _label_by_key(key: str) -> str:
        mapping = {
            "min_server_time": "Минимальное время на сервере",
            "min_voice_time": "Минимальное время в голосе",
            "required_role": "Необходимая роль",
            "min_level": "Минимальный уровень",
            "booster_only": "Только для бустеров",
            "no_revote": "Запрет на повторное участие",
        }
        return mapping.get(key, key)

class GiveawayParticipationView(discord.ui.View):
    """Бессрочная вьюха для участия в розыгрыше."""

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
        if not self.giveaway_id:
            await interaction.response.send_message(
                "Не удалось определить розыгрыш.", ephemeral=True
            )
            return

        giveaway = await self.manager.get_giveaway(self.giveaway_id)
        if not giveaway or giveaway["is_ended"]:
            await interaction.response.send_message(
                "Этот розыгрыш уже завершён.", ephemeral=True
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
                f"{Emojis.GIVEAWAY} Вы не можете участвовать.\n- {result.get('reason', 'Причина не указана')}",
                ephemeral=True,
            )
            return

        status = await self.manager.toggle_participation(
            self.giveaway_id, str(interaction.user.id)
        )
        if status == "inactive":
            await interaction.response.send_message(
                "Розыгрыш уже завершён.", ephemeral=True
            )
            return

        participants = await self.manager.repo.list_participants(self.giveaway_id)
        self.count = len(participants)
        self.join_button.label = f"Участвовать ({self.count})"

        message = (
            f"{Emojis.GIVEAWAY} Вы участвуете в розыгрыше!"
            if status == "joined"
            else f"{Emojis.GIVEAWAY} Вы отказались от участия."
        )
        await interaction.response.send_message(message, ephemeral=True)
        if interaction.message:
            await interaction.message.edit(view=self)

    async def handle_list(self, interaction: discord.Interaction):
        await self.ensure_manager(interaction)
        await self.ensure_giveaway_id(interaction)
        if not self.giveaway_id:
            await interaction.response.send_message(
                "Не удалось определить розыгрыш.", ephemeral=True
            )
            return

        giveaway = await self.manager.get_giveaway(self.giveaway_id)
        if not giveaway:
            await interaction.response.send_message(
                "Розыгрыш не найден.", ephemeral=True
            )
            return

        participants = await self.manager.repo.list_participants(self.giveaway_id)
        winners_count = giveaway.get("winners_count", 1)
        if not participants:
            await interaction.response.send_message(
                f"{Emojis.GIVEAWAY} В розыгрыше пока нет участников.",
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
            footer = f"Страница {page_idx + 1}/{len(pages)}" if len(pages) > 1 else ""
            embed = Embed(
                title=f"{Emojis.GIVEAWAY} Участники розыгрыша",
                description=(
                    f"Всего участников: **{len(participants)}**\n"
                    f"Призовых мест: **{winners_count}**\n" + "\n".join(page_lines)
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
