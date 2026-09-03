import discord
from typing import Iterable, Optional
from Niludetsu.locale import _

TEMP_OPTIONS = [
    discord.SelectOption(
        label="Передать права",
        description="Передача владения каналом другому участнику",
        emoji="👑",
        value="transfer",
    ),
    discord.SelectOption(
        label="Управление доступом",
        description="Добавить или удалить участников",
        emoji="🛡️",
        value="access",
    ),
    discord.SelectOption(
        label="Изменить лимит",
        description="Установить количество слотов",
        emoji="🔢",
        value="limit",
    ),
    discord.SelectOption(
        label="Закрыть / открыть",
        description="Заблокировать или разблокировать канал",
        emoji="🔒",
        value="lock_channel",
    ),
    discord.SelectOption(
        label="Сохранение настроек",
        description="Переключить запоминание настроек канала",
        emoji="💾",
        value="remember_toggle",
    ),
    discord.SelectOption(
        label="Переименовать",
        description="Изменить название канала",
        emoji="✏️",
        value="rename",
    ),
    discord.SelectOption(
        label="Создать приглашение",
        description="Сгенерировать приглашение на 24 часа",
        emoji="🔗",
        value="invite",
    ),
    discord.SelectOption(
        label="Создать текстовый канал",
        description="Открыть чат для обсуждений",
        emoji="🧵",
        value="thread",
    ),
    discord.SelectOption(
        label="Удалить канал",
        description="Удалить временный канал",
        emoji="🗑️",
        value="delete",
    ),
]

class RenameModal(discord.ui.Modal, title="Переименовать канал"):
    new_name = discord.ui.TextInput(
        label="Новое название",
        max_length=90,
        placeholder="Например: 🔊 Chill",
    )

    def __init__(self, service, channel: discord.VoiceChannel) -> None:
        super().__init__(timeout=300)
        self.service = service
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction) -> None:
        t = _(ctx=interaction)
        await interaction.response.defer(ephemeral=True)
        await self.service.rename(self.channel, str(self.new_name.value))
        await interaction.followup.send(t("temprooms", "name_updated"), ephemeral=True)

class LimitModal(discord.ui.Modal, title="Изменить лимит"):
    limit = discord.ui.TextInput(
        label="Максимум участников",
        placeholder="0 - без лимита",
        max_length=2,
    )

    def __init__(self, service, channel: discord.VoiceChannel) -> None:
        super().__init__(timeout=300)
        self.service = service
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction) -> None:
        t = _(ctx=interaction)
        await interaction.response.defer(ephemeral=True)
        try:
            value = int(str(self.limit.value).strip())
        except ValueError:
            await interaction.followup.send(t("temprooms", "limit_invalid"), ephemeral=True)
            return
        await self.service.set_limit(self.channel, value)
        limit_text = str(value) if value else t("temprooms", "limit_no_limit")
        await interaction.followup.send(t("temprooms", "limit_set", limit=limit_text), ephemeral=True)

class AccessModal(discord.ui.Modal, title="Управление доступом"):
    mode = discord.ui.TextInput(
        label="Режим (open / allowlist / denylist)",
        default="open",
        max_length=20,
    )
    users = discord.ui.TextInput(
        label="ID или @упоминания (через пробел)",
        style=discord.TextStyle.paragraph,
        required=False,
    )

    def __init__(self, service, channel: discord.VoiceChannel) -> None:
        super().__init__(timeout=300)
        self.service = service
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction) -> None:
        t = _(ctx=interaction)
        await interaction.response.defer(ephemeral=True)
        raw_users = str(self.users.value or "").replace("<@", "").replace(">", "")
        user_ids: Iterable[int] = []
        if raw_users:
            user_ids = {int(item) for item in raw_users.split() if item.isdigit()}

        room = await self.service.update_access(
            self.channel,
            mode=str(self.mode.value).strip().lower(),
            user_ids=user_ids,
        )
        await interaction.followup.send(
            t("temprooms", "access_updated", mode=room.access_mode, count=len(room.access_list)),
            ephemeral=True,
        )

class TransferSelect(discord.ui.Select):
    def __init__(self, service, channel: discord.VoiceChannel, room):
        options = []
        for member in channel.members:
            if str(member.id) == room.owner_id or member.bot:
                continue
            options.append(discord.SelectOption(label=member.display_name, value=str(member.id)))

        if not options:
            options = [discord.SelectOption(label="Нет доступных участников", value="none", default=True)]

        super().__init__(
            placeholder="Выбери нового владельца",
            options=options,
            min_values=1,
            max_values=1,
        )
        self.service = service
        self.channel = channel
        self.room = room

    async def callback(self, interaction: discord.Interaction) -> None:
        t = _(ctx=interaction)
        if self.values[0] == "none":
            # Обновляем селектор и показываем сообщение об отсутствии кандидатов
            self.disabled = True
            self.placeholder = t("temprooms", "no_members_option")
            try:
                await interaction.response.edit_message(view=self.view)
            except Exception:
                pass
            await interaction.followup.send(t("temprooms", "no_one_in_channel"), ephemeral=True)
            return
        new_owner_id = int(self.values[0])
        new_owner = self.channel.guild.get_member(new_owner_id)
        if not new_owner:
            try:
                self.disabled = True
                self.placeholder = t("temprooms", "member_not_found")
                await interaction.response.edit_message(view=self.view)
            except Exception:
                await interaction.response.send_message(t("temprooms", "member_not_found_msg"), ephemeral=True)
            return

        await self.service.repo.update_room(str(self.channel.id), owner_id=str(new_owner_id))
        await self.service._apply_permissions(self.channel)
        self.service.invalidate_room(str(self.channel.id))

        # Блокируем селектор для предотвращения повторных действий и обновляем текст
        self.disabled = True
        self.placeholder = t("temprooms", "new_owner", name=new_owner.display_name)
        try:
            await interaction.response.edit_message(view=self.view)
        except Exception:
            pass
        await interaction.followup.send(
            t("temprooms", "transferred", name=new_owner.display_name), ephemeral=True
        )

class TransferView(discord.ui.View):
    def __init__(self, service, channel: discord.VoiceChannel, room):
        super().__init__(timeout=120)
        self.add_item(TransferSelect(service, channel, room))

class TempRoomActions(discord.ui.View):
    message: Optional[discord.Message]
    owner_id: Optional[int]

    def __init__(self, service) -> None:
        super().__init__(timeout=None)
        self.service = service
        self.message = None
        self.owner_id = None

        self.selector = discord.ui.Select(
            placeholder="Выберите действие",
            options=TEMP_OPTIONS,
            min_values=1,
            max_values=1,
            custom_id="temproom:select",
        )
        self.selector.callback = self.on_select  # type: ignore
        self.add_item(self.selector)

    async def bind_message(self, message: discord.Message, owner: discord.Member) -> None:
        """Привязываем view к сообщению и конкретному владельцу."""
        self.message = message
        self.owner_id = owner.id
        await self.sync_view()

    async def reset_context(self) -> None:
        """Сбрасываем, если вид передали другому владельцу или канал удалён."""
        self.message = None
        self.owner_id = None

    async def sync_view(self) -> None:
        if self.message:
            await self.message.edit(view=self)

    def _clone_options(self) -> list[discord.SelectOption]:
        cloned: list[discord.SelectOption] = []
        for o in self.selector.options:
            cloned.append(
                discord.SelectOption(
                    label=o.label,
                    value=o.value,
                    description=o.description,
                    emoji=o.emoji,
                    default=False,
                )
            )
        return cloned

    def _reset_selector(self) -> None:
        old = self.selector
        new = discord.ui.Select(
            placeholder=old.placeholder,
            options=self._clone_options(),
            min_values=old.min_values,
            max_values=old.max_values,
            custom_id=old.custom_id,
        )
        new.callback = self.on_select  # type: ignore
        self.remove_item(old)
        self.selector = new
        self.add_item(new)

    async def _edit_via_interaction(self, interaction: discord.Interaction) -> None:
        try:
            if interaction.message:
                await interaction.message.edit(view=self)
        except Exception:
            pass

    async def on_select(self, interaction: discord.Interaction) -> None:
        t = _(ctx=interaction)
        voice = self._resolve_channel(interaction)
        if voice is None:
            await interaction.response.send_message(t("temprooms", "not_in_voice"), ephemeral=True)
            self._reset_selector()
            await self._edit_via_interaction(interaction)
            return

        room = await self.service.get_room(voice.id)
        if not room or str(interaction.user.id) != room.owner_id:
            await interaction.response.send_message(t("temprooms", "not_owner"), ephemeral=True)
            self._reset_selector()
            await self._edit_via_interaction(interaction)
            return

        if self.owner_id and self.owner_id != interaction.user.id:
            # Панель подвязана на предыдущего владельца → сбрасываем и сообщаем пользователю
            await self.reset_context()
            await interaction.response.send_message(
                t("temprooms", "panel_expired"),
                ephemeral=True,
            )
            return

        action = self.selector.values[0]

        if action in {"rename", "limit", "access"}:
            # Сбрасываем выбор перед открытием модалки
            self._reset_selector()
            await self._edit_via_interaction(interaction)
            modals = {
                "rename": RenameModal(self.service, voice),
                "limit": LimitModal(self.service, voice),
                "access": AccessModal(self.service, voice),
            }
            await interaction.response.send_modal(modals[action])
            return

        await interaction.response.defer(ephemeral=True, thinking=True)
        # Всегда сбрасываем селектор после выбора действия
        self._reset_selector()
        await self._edit_via_interaction(interaction)

        if action == "lock_channel":
            room = await self.service.toggle_lock(voice)
            state = t("temprooms", "channel_closed") if room.locked else t("temprooms", "channel_opened")
            await interaction.followup.send(t("temprooms", "channel_state", state=state), ephemeral=True)
            return

        if action == "invite":
            invite = await self.service.create_invite(voice)
            await interaction.followup.send(t("temprooms", "invite_created", url=invite.url), ephemeral=True)
            return

        if action == "thread":
            room = await self.service.create_thread(voice, owner=interaction.user)  # type: ignore[arg-type]
            if room.thread_id:
                await interaction.followup.send(t("temprooms", "thread_created"), ephemeral=True)
            else:
                await interaction.followup.send(t("temprooms", "thread_exists"), ephemeral=True)
            return

        if action == "remember_toggle":
            room = await self.service.toggle_remember(voice)
            state = t("temprooms", "remember_enabled") if room.remember_settings else t("temprooms", "remember_disabled")
            await interaction.followup.send(t("temprooms", "remember_state", state=state), ephemeral=True)
            return

        if action == "transfer":
            room = await self.service.require_room(voice)
            view = TransferView(self.service, voice, room)
            await interaction.followup.send(t("temprooms", "select_new_owner"), view=view, ephemeral=True)
            return

        if action == "delete":
            await self.service.delete_temp_room(voice)
            await interaction.followup.send(t("temprooms", "channel_deleted"), ephemeral=True)
            return

    def _resolve_channel(self, interaction: discord.Interaction) -> Optional[discord.VoiceChannel]:
        if isinstance(interaction.user, discord.Member):
            state = interaction.user.voice
            if state and isinstance(state.channel, discord.VoiceChannel):
                return state.channel
        return None

