import asyncio, discord
from dataclasses import dataclass
from discord.ext import tasks
from Niludetsu import Time
from Niludetsu.analytics.repository import AnalyticsRepository
from Niludetsu.temprooms.cache import TempRoomCache
from Niludetsu.temprooms.repository import TempRoomsRepository
from typing import Dict, Optional

_time = Time()

@dataclass
class VoiceState:
    channel_id: str
    joined_at_ts: float
    joined_at_iso: str

class AnalyticsTracker:
    """Записывает сообщения и голосовую активность в user_analytics."""

    def __init__(self, bot: discord.Client, *, main_guild_id: Optional[int] = None) -> None:
        self.bot = bot
        self.main_guild_id = main_guild_id
        self.repo = AnalyticsRepository()
        self.voice_states: Dict[int, VoiceState] = {}
        self._lock = asyncio.Lock()
        self.flush_voice_sessions.start()
        self.temp_repo = TempRoomsRepository()
        self.temp_cache = TempRoomCache(ttl=15.0)

    def cog_unload(self) -> None:
        self.flush_voice_sessions.cancel()
        self.voice_states.clear()

    async def track_message(self, guild_id: str, user_id: str, channel_id: str) -> None:
        if self.main_guild_id and int(guild_id) != self.main_guild_id:
            return
        temp_key = await self._channel_key(channel_id)
        await self.repo.upsert_user_row(
            guild_id,
            user_id,
            add_messages=1,
            message_channel=temp_key,
        )

    async def track_message_delete(self, guild_id: str, user_id: str, channel_id: str) -> None:
        if self.main_guild_id and int(guild_id) != self.main_guild_id:
            return
        temp_key = await self._channel_key(channel_id)
        await self.repo.upsert_user_row(
            guild_id,
            user_id,
            add_deleted=1,
            add_messages=-1,
            message_channel=temp_key,
        )

    async def track_voice_join(self, member: discord.Member, channel: discord.VoiceChannel) -> None:
        if member.bot or (self.main_guild_id and member.guild.id != self.main_guild_id):
            return

        guild_id = str(member.guild.id)
        user_id = str(member.id)

        await self.repo.upsert_user_row(guild_id, user_id)
        async with self._lock:
            prev_state = self.voice_states.get(member.id)
        if prev_state:
            try:
                await self._commit_voice_time(member, prev_state)
            finally:
                async with self._lock:
                    self.voice_states.pop(member.id, None)

        joined = _time.now()
        state = VoiceState(
            channel_id=str(channel.id),
            joined_at_ts=float(joined.timestamp()),
            joined_at_iso=_time.to_iso(joined),
        )
        async with self._lock:
            self.voice_states[member.id] = state

        await self.repo.set_last_voice_join(guild_id, user_id, state.joined_at_iso)

    async def track_voice_leave(self, member: discord.Member) -> None:
        if member.bot:
            return

        async with self._lock:
            state = self.voice_states.pop(member.id, None)

        if not state:
            return

        await self._commit_voice_time(member, state)
        await self.repo.set_last_voice_join(str(member.guild.id), str(member.id), None)

    async def _commit_voice_time(self, member: discord.Member, state: VoiceState) -> int:
        now_dt = _time.now()
        now_ts = float(now_dt.timestamp())
        elapsed = max(now_ts - state.joined_at_ts, 0.0)
        seconds = int(elapsed)

        if seconds <= 0:
            return 0

        channel_key = await self._channel_key(state.channel_id)
        await self.repo.upsert_user_row(
            str(member.guild.id),
            str(member.id),
            add_voice_seconds=seconds,
            voice_channel=channel_key,
        )

        state.joined_at_ts = now_ts
        state.joined_at_iso = _time.to_iso(now_dt)
        return seconds

    @tasks.loop(seconds=3)
    async def flush_voice_sessions(self) -> None:
        if not self.voice_states:
            return

        async with self._lock:
            snapshot = dict(self.voice_states)

        for user_id, state in snapshot.items():
            member = None
            for guild in self.bot.guilds:
                member = guild.get_member(user_id)
                if member:
                    break

            if not member or member.bot or not member.voice or not member.voice.channel:
                continue

            added = await self._commit_voice_time(member, state)
            if added > 0:
                async with self._lock:
                    self.voice_states[user_id] = state

    @flush_voice_sessions.before_loop
    async def before_flush_voice_sessions(self) -> None:
        await self.bot.wait_until_ready()
        await asyncio.sleep(1.0)

    async def _channel_key(self, channel_id: str) -> str:
        try:
            is_temp = await self._is_temp_channel(channel_id)
        except Exception:
            return str(channel_id)
        return f"temp_{channel_id}" if is_temp else str(channel_id)

    async def _is_temp_channel(self, channel_id: str) -> bool:
        cached = self.temp_cache.get(channel_id)
        if cached is True:
            return True
        if cached is False:
            pass

        try:
            row = await self.temp_repo.get_room_row(channel_id)
        except Exception:
            return False

        if row:
            self.temp_cache.set(channel_id, True)
            return True

        return False

