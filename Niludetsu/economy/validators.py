import asyncio
from Niludetsu.economy.manager import EconomyManager
from Niludetsu.tools.Embed import Embed
from Niludetsu.locale import _
from typing import Callable, Dict, Optional, Tuple

class GameSessionRegistry:
    """Хранит активные игровые сессии (game_name + user + guild)."""

    def __init__(self) -> None:
        self._sessions: Dict[Tuple[str, str, str], str] = {}
        self._lock = asyncio.Lock()

    def _key(self, game_name: str, user_id: str, guild_id: str) -> Tuple[str, str, str]:
        return game_name.lower(), str(user_id), str(guild_id)

    async def claim(self, game_name: str, user_id: str, guild_id: str) -> bool:
        async with self._lock:
            key = self._key(game_name, user_id, guild_id)
            if key in self._sessions:
                return False
            self._sessions[key] = game_name
            return True

    async def release(self, game_name: str, user_id: str, guild_id: str) -> None:
        async with self._lock:
            self._sessions.pop(self._key(game_name, user_id, guild_id), None)

    async def has_active(self, game_name: str, user_id: str, guild_id: str) -> bool:
        async with self._lock:
            return self._key(game_name, user_id, guild_id) in self._sessions

class EconomyValidator:
    """Управление игровыми сессиями."""

    def __init__(self, economy: EconomyManager):
        self.economy = economy
        self._sessions = GameSessionRegistry()

    async def claim_game(self, game_name: str, user_id: str, guild_id: str, t: Optional[Callable] = None) -> Tuple[bool, Optional[Embed]]:
        if t is None:
            t = _(guild_id=guild_id)
        if not await self._sessions.claim(game_name, user_id, guild_id):
            return False, Embed.error(
                t("economy_validators", "active_game", game=game_name)
            )
        return True, None

    async def release_game(self, game_name: str, user_id: str, guild_id: str) -> None:
        await self._sessions.release(game_name, user_id, guild_id)

    async def has_active_game(self, game_name: str, user_id: str, guild_id: str) -> bool:
        return await self._sessions.has_active(game_name, user_id, guild_id)
