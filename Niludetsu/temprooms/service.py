from __future__ import annotations
import discord
from dataclasses import dataclass
from discord.utils import escape_markdown, get
from Niludetsu import config
from Niludetsu.temprooms.cache import TempRoomCache
from Niludetsu.temprooms.repository import TempRoomsRepository
from Niludetsu.tools.Time import TimeService
from typing import Iterable, Optional

_time = TimeService()

@dataclass(slots=True)
class TempRoom:
    channel_id: str
    guild_id: str
    owner_id: str
    name: str
    user_limit: int
    is_private: bool
    remember_settings: bool
    locked: bool
    access_mode: str
    access_list: list[str]
    thread_id: Optional[str]
    active: bool

    @classmethod
    def from_row(cls, row: dict) -> TempRoom:
        return cls(
            channel_id=row["channel_id"],
            guild_id=row["guild_id"],
            owner_id=row["owner_id"],
            name=row.get("name", config.TEMPROOM_DEFAULT_NAME),
            user_limit=int(row.get("user_limit", 0) or 0),
            is_private=bool(row.get("is_private", False)),
            remember_settings=bool(row.get("remember_settings", False)),
            locked=bool(row.get("locked", False)),
            access_mode=row.get("access_mode", "open"),
            access_list=list(row.get("access_list") or []),
            thread_id=row.get("thread_id"),
            active=bool(row.get("active", True)),
        )

class TempRoomService:
    """Высокоуровневое управление временными голосовыми каналами."""

    def __init__(self, bot: discord.Client) -> None:
        self.bot = bot
        self.repo = TempRoomsRepository()
        self.cache = TempRoomCache(ttl=15.0)

    # Получение / кеш 

    async def get_room(self, channel_id: int | str) -> Optional[TempRoom]:
        key = str(channel_id)
        cached = self.cache.get(key)
        if cached is not None:
            return cached

        row = await self.repo.get_room_row(key)
        if not row or not row.get("active", True):
            self.cache.invalidate(key)
            return None

        room = TempRoom.from_row(row)
        self.cache.set(key, room)
        return room

    async def require_room(self, channel: discord.VoiceChannel) -> TempRoom:
        room = await self.get_room(channel.id)
        if not room:
            raise RuntimeError("Temp room not registered")
        return room

    def invalidate_room(self, channel_id: str) -> None:
        self.cache.invalidate(str(channel_id))

    # Создание / удаление 
    async def create_temp_room(self, member: discord.Member) -> discord.VoiceChannel:
        guild = member.guild

        existing = await self.repo.db.where(
            "temprooms",
            filters=[
                {"column": "guild_id", "value": str(guild.id)},
                {"column": "owner_id", "value": str(member.id)},
                {"column": "active", "value": "true", "op": "is"},
            ],
            limit=1,
        )
        if existing:
            room = TempRoom.from_row(existing[0])
            channel = guild.get_channel(int(room.channel_id))
            if isinstance(channel, discord.VoiceChannel):
                await member.move_to(channel, reason="Перемещение в уже созданный временный канал")
                return channel
            await self.repo.deactivate_room(str(room.channel_id))
            self.invalidate_room(str(room.channel_id))

        # ищем последнюю комнату с remember_settings 
        remembered: Optional[dict] = None
        history = await self.repo.db.where(
            "temprooms",
            filters=[
                {"column": "guild_id", "value": str(guild.id)},
                {"column": "owner_id", "value": str(member.id)},
            ],
            order=[{"column": "updated_at", "ascending": False}],
            limit=1,
        )
        if history and history[0].get("remember_settings"):
            remembered = history[0]

        category_id = getattr(config, "TEMPROOM_CATEGORY", None)
        channel_template = getattr(config, "TEMPROOM_DEFAULT_NAME", "🔊 {name}")
        category = get(guild.categories, id=category_id) if category_id else None
        if category is None:
            raise RuntimeError("Temp room category is not configured or missing")

        channel_name = self._format_name(channel_template, member)
        if remembered and remembered.get("name"):
            channel_name = remembered["name"]

        overwrites = self._base_overwrites(guild, member)

        voice_channel = await guild.create_voice_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites,
            user_limit=int(remembered.get("user_limit", 0) if remembered else 0),
            reason="Создан временный канал",
        )

        await self.repo.ensure_room(
            channel_id=voice_channel.id,
            guild_id=guild.id,
            owner_id=member.id,
            name=voice_channel.name,
        )
        if remembered:
            await self.repo.update_room(
                str(voice_channel.id),
                remember_settings=True,
                is_private=bool(remembered.get("is_private", False)),
                locked=bool(remembered.get("locked", False)),
                access_mode=remembered.get("access_mode", "open"),
                access_list=remembered.get("access_list") or [],
                user_limit=int(remembered.get("user_limit") or 0),
            )
            await self._apply_permissions(
                voice_channel,
                locked=bool(remembered.get("locked", False)),
                is_private=bool(remembered.get("is_private", False)),
                access_mode=remembered.get("access_mode", "open"),
                access_list=remembered.get("access_list") or [],
            )

        self.invalidate_room(str(voice_channel.id))
        await member.move_to(voice_channel, reason="Перемещение в временный канал")
        return voice_channel

    async def delete_temp_room(self, channel: discord.VoiceChannel, *, reason: str = "Удаление временного канала") -> None:
        room = await self.get_room(channel.id)
        thread_id = room.thread_id if room else None

        try:
            await channel.delete(reason=reason)
        finally:
            await self.repo.deactivate_room(str(channel.id))
            self.invalidate_room(str(channel.id))

        if thread_id:
            thread = channel.guild.get_channel(int(thread_id))
            if thread:
                await thread.delete(reason="Удаление канала временной комнаты")

    # Настройки 

    async def rename(self, channel: discord.VoiceChannel, new_name: str) -> TempRoom:
        new_name = new_name.strip() or channel.name
        await channel.edit(name=new_name)
        await self.repo.update_room(str(channel.id), name=new_name)
        self.invalidate_room(str(channel.id))
        return await self.require_room(channel)

    async def set_limit(self, channel: discord.VoiceChannel, limit: int) -> TempRoom:
        limit = max(0, min(limit, 99))
        await channel.edit(user_limit=limit)
        await self.repo.update_room(str(channel.id), user_limit=limit)
        self.invalidate_room(str(channel.id))
        return await self.require_room(channel)

    async def toggle_lock(self, channel: discord.VoiceChannel) -> TempRoom:
        room = await self.require_room(channel)
        new_state = not room.locked
        await self.repo.update_room(str(channel.id), locked=new_state)
        await self._apply_permissions(channel, locked=new_state, is_private=room.is_private, access_mode=room.access_mode)
        self.invalidate_room(str(channel.id))
        return await self.require_room(channel)

    async def switch_privacy(self, channel: discord.VoiceChannel, private: bool) -> TempRoom:
        room = await self.require_room(channel)
        await self.repo.update_room(str(channel.id), is_private=private)
        await self._apply_permissions(channel, locked=room.locked, is_private=private, access_mode=room.access_mode, access_list=room.access_list)
        self.invalidate_room(str(channel.id))
        return await self.require_room(channel)

    async def toggle_remember(self, channel: discord.VoiceChannel) -> TempRoom:
        room = await self.require_room(channel)
        new_value = not room.remember_settings
        await self.repo.update_room(str(channel.id), remember_settings=new_value)
        self.invalidate_room(str(channel.id))
        return await self.require_room(channel)

    async def update_access(
        self,
        channel: discord.VoiceChannel,
        *,
        mode: str,
        user_ids: Optional[Iterable[int]] = None,
    ) -> TempRoom:
        mode = mode if mode in {"open", "allowlist", "denylist"} else "open"
        access_list = [str(x) for x in (user_ids or [])]
        await self.repo.update_room(
            str(channel.id),
            access_mode=mode,
            access_list=access_list,
        )
        await self._apply_permissions(channel, access_mode=mode, access_list=access_list)
        self.invalidate_room(str(channel.id))
        return await self.require_room(channel)

    async def create_thread(self, channel: discord.VoiceChannel, *, owner: discord.Member) -> TempRoom:
        room = await self.require_room(channel)
        if room.thread_id:
            existing = channel.guild.get_channel(int(room.thread_id))
            if existing:
                return room

        category = None
        thread_category_id = getattr(config, "TEMPROOM_THREAD_CATEGORY", None)
        if thread_category_id:
            category = discord.utils.get(channel.guild.channels, id=thread_category_id)

        text_channel = await channel.guild.create_text_channel(
            name=f"voice-{channel.name}",
            category=category or channel.category,
            reason="Создание текстового канала для временного голоса",
        )
        await text_channel.set_permissions(owner, manage_channels=True, send_messages=True, read_messages=True)

        await self.repo.update_room(str(channel.id), thread_id=str(text_channel.id))
        self.invalidate_room(str(channel.id))
        return await self.require_room(channel)

    async def create_invite(self, channel: discord.VoiceChannel) -> discord.Invite:
        lifetime = getattr(config, "TEMPROOM_INVITE_LIFETIME", 86400)
        invite = await channel.create_invite(
            max_age=lifetime,
            max_uses=0,
            unique=True,
            reason="Приглашение в временный голосовой канал",
        )
        return invite

    # Вспомогательные 

    def _format_name(self, template: str, member: discord.Member) -> str:
        safe_name = escape_markdown(member.display_name) or member.name
        result = template.replace("{name}", safe_name).replace("{user}", safe_name)
        return result[:90]

    def _base_overwrites(self, guild: discord.Guild, owner: discord.Member) -> dict[discord.abc.Snowflake, discord.PermissionOverwrite]:
        overwrites: dict[discord.abc.Snowflake, discord.PermissionOverwrite] = {
            guild.default_role: discord.PermissionOverwrite(connect=True, view_channel=True),
            owner: discord.PermissionOverwrite(connect=True, move_members=True, manage_channels=True, mute_members=True),
        }

        # Закрываем канал для забаненных пользователей
        ban_role_id = getattr(config, "BAN_ROLE_ID", None)
        if ban_role_id:
            ban_role = guild.get_role(ban_role_id)
            if ban_role:
                overwrites[ban_role] = discord.PermissionOverwrite(view_channel=False, connect=False)

        return overwrites

    async def _apply_permissions(
        self,
        channel: discord.VoiceChannel,
        *,
        locked: Optional[bool] = None,
        is_private: Optional[bool] = None,
        access_mode: Optional[str] = None,
        access_list: Optional[Iterable[str]] = None,
    ) -> None:
        room = await self.get_room(channel.id)
        locked = room.locked if locked is None else locked
        is_private = room.is_private if is_private is None else is_private
        access_mode = room.access_mode if access_mode is None else access_mode
        access_list = list(room.access_list if access_list is None else access_list)

        overwrites = channel.overwrites
        default_role = channel.guild.default_role

        # Базовый сценарий: все видят, все могут подключаться
        base_connect = not locked and not is_private
        overwrites[default_role] = discord.PermissionOverwrite(
            view_channel=not is_private,
            connect=base_connect,
        )

        owner = channel.guild.get_member(int(room.owner_id)) if room else None
        if owner:
            overwrites[owner] = discord.PermissionOverwrite(
                view_channel=True,
                connect=True,
                manage_channels=True,
                move_members=True,
            )

        # allow/deny списки
        if access_mode == "allowlist":
            overwrites[default_role].connect = False
            for user_id in access_list:
                member = channel.guild.get_member(int(user_id))
                if member:
                    overwrites[member] = discord.PermissionOverwrite(connect=True, view_channel=True)
        elif access_mode == "denylist":
            for user_id in access_list:
                member = channel.guild.get_member(int(user_id))
                if member:
                    overwrites[member] = discord.PermissionOverwrite(connect=False)

        # Всегда закрываем канал для забаненных пользователей
        ban_role_id = getattr(config, "BAN_ROLE_ID", None)
        if ban_role_id:
            ban_role = channel.guild.get_role(ban_role_id)
            if ban_role:
                overwrites[ban_role] = discord.PermissionOverwrite(view_channel=False, connect=False)

        await channel.edit(overwrites=overwrites)

