import asyncio
import time as pytime
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
from ..logging import logger
from ..tools.Time import TimeService as Time

import discord
from discord.ext import tasks

from Niludetsu.analytics.repository import AnalyticsRepository

from Niludetsu.quests.tracker import QuestTracker

_time = Time()

@dataclass
class VoiceState:
    channel_id: str
    joined_at_ts: float
    joined_at_iso: str

class AnalyticsTracker:

    def __init__(self, bot: discord.Client, *, main_guild_id: Optional[int] = None) -> None:
        self.bot = bot
        self.main_guild_id = main_guild_id
        self.repo = AnalyticsRepository()
        self.voice_states: Dict[int, VoiceState] = {}
        
        self._msg_buffer: Dict[Tuple[str, str, str], int] = {}
        self._buffer_lock = asyncio.Lock()
        
        self.flush_tasks.start()
        
        self.quest_tracker = QuestTracker()
        self._voice_quest_accum: Dict[int, int] = {}

    def cog_unload(self) -> None:
        self.flush_tasks.cancel()

    async def track_message(self, guild_id: str, user_id: str, channel_id: str) -> None:
        if not self._is_main_guild(guild_id):
            return

        key = self._message_key(guild_id, user_id, channel_id)
        async with self._buffer_lock:
            self._msg_buffer[key] = self._msg_buffer.get(key, 0) + 1

    @tasks.loop(seconds=30)
    async def flush_tasks(self) -> None:
        await asyncio.gather(
            self._flush_messages(),
            self._flush_voice()
        )

    async def _flush_messages(self) -> None:
        async with self._buffer_lock:
            if not self._msg_buffer:
                return
            current_buffer = self._msg_buffer.copy()
            self._msg_buffer.clear()

        await self._flush_message_batch(current_buffer)

    async def flush_user(self, guild_id: str, user_id: str) -> None:
        target = (str(guild_id), str(user_id))
        selected: Dict[Tuple[str, str, str], int] = {}

        async with self._buffer_lock:
            for key, count in list(self._msg_buffer.items()):
                gid, uid, _ = key
                if (gid, uid) != target:
                    continue
                selected[key] = count
                del self._msg_buffer[key]

        if selected:
            await self._flush_message_batch(selected)

    async def _flush_message_batch(
        self,
        batch: Dict[Tuple[str, str, str], int],
    ) -> None:
        for (gid, uid, cid), count in batch.items():
            try:
                await self.repo.upsert_user_row(
                    gid,
                    uid,
                    add_messages=count,
                    message_channel=cid,
                )
            except Exception as e:
                logger.error(f"Error flushing analytics for {uid}: {e}")

    async def _flush_voice(self) -> None:
        if not self.voice_states:
            return

        snapshot = list(self.voice_states.items())
        for user_id, state in snapshot:
            member = self._find_member(user_id)
            if not member or not member.voice or not member.voice.channel:
                continue
            await self._commit_voice_time(member, state)

    def _find_member(self, user_id: int) -> Optional[discord.Member]:
        for guild in self.bot.guilds:
            member = guild.get_member(user_id)
            if member:
                return member
        return None

    def _is_main_guild(self, guild_id: str | int) -> bool:
        return not self.main_guild_id or int(guild_id) == self.main_guild_id

    def _message_key(
        self,
        guild_id: str | int,
        user_id: str | int,
        channel_id: str | int,
    ) -> Tuple[str, str, str]:
        return str(guild_id), str(user_id), str(channel_id)

    async def _commit_voice_time(self, member: discord.Member, state: VoiceState) -> None:
        now_ts = pytime.time()
        seconds = int(now_ts - state.joined_at_ts)
        if seconds <= 0:
            return

        await self.repo.upsert_user_row(
            str(member.guild.id),
            str(member.id),
            add_voice_seconds=seconds,
            voice_channel=state.channel_id,
        )
        now_iso = _time.to_iso()
        await self.repo.set_last_voice_join(
            str(member.guild.id),
            str(member.id),
            now_iso,
        )

        state.joined_at_ts = now_ts
        state.joined_at_iso = now_iso
        
        accum = self._voice_quest_accum.get(member.id, 0) + seconds
        minutes = accum // 60
        if minutes > 0:
            asyncio.create_task(self.quest_tracker.on_voice_minute(str(member.guild.id), str(member.id), minutes))
        self._voice_quest_accum[member.id] = accum % 60

    async def track_voice_join(self, member: discord.Member, channel: discord.VoiceChannel) -> None:
        if member.bot or not self._is_main_guild(member.guild.id):
            return
        
        now_iso = _time.to_iso()
        state = VoiceState(str(channel.id), pytime.time(), now_iso)
        self.voice_states[member.id] = state
        await self.repo.set_last_voice_join(str(member.guild.id), str(member.id), now_iso)

    async def track_voice_leave(self, member: discord.Member) -> None:
        state = self.voice_states.pop(member.id, None)
        if state:
            await self._commit_voice_time(member, state)
            await self.repo.set_last_voice_join(str(member.guild.id), str(member.id), None)

    async def track_message_delete(self, guild_id: str, user_id: str, channel_id: str) -> None:
        if not self._is_main_guild(guild_id):
            return

        try:
            await self.repo.upsert_user_row(
                str(guild_id),
                str(user_id),
                add_deleted=1,
                message_channel=str(channel_id),
            )
        except Exception as e:
            logger.error(f"Error tracking deleted message for {user_id}: {e}")

    @flush_tasks.before_loop
    async def _before_flush_tasks(self) -> None:
        await self.bot.wait_until_ready()
