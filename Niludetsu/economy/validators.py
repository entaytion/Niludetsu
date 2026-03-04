import asyncio
from Niludetsu.economy.manager import EconomyManager
from Niludetsu.tools.Embed import Embed
from Niludetsu.tools.Emojis import Emojis
from typing import Dict, Optional, Tuple, Union

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
    """Валидации ставок, переводов и управление игровыми сессиями."""

    def __init__(self, economy: EconomyManager):
        self.economy = economy
        self._sessions = GameSessionRegistry()

    # Ставки 
    async def validate_bet(
        self,
        bet: Union[str, int, None],
        user_id: str,
        guild_id: str,
    ) -> Tuple[bool, int, Optional[Embed]]:
        bet_str = str(bet).strip() if bet is not None else ""
        if not bet_str:
            return False, 0, Embed.error(f"Ставка не может быть пустой! Пример: 100 {Emojis.MONEY}")
        if any(symbol in bet_str for symbol in (".", ",")):
            return False, 0, Embed.error(f"Ставка должна быть целым числом! Пример: 100 {Emojis.MONEY}")
        if bet_str.startswith("-") or (len(bet_str) > 1 and bet_str.startswith("0")):
            return False, 0, Embed.error(f"Только положительные числа! Пример: 100 {Emojis.MONEY}")
        if not bet_str.isdigit():
            return False, 0, Embed.error("Ставка должна содержать только цифры")

        bet_value = int(bet_str)
        if bet_value < 1:
            return False, 0, Embed.error(f"Минимальная ставка — 1 {Emojis.MONEY}")

        balance = await self.economy.get_wallet(user_id, guild_id)
        if balance < bet_value:
            return False, 0, Embed.error(
                f"Недостаточно средств! Баланс {balance:,} {Emojis.MONEY}, требуется {bet_value:,} {Emojis.MONEY}"
            )
        return True, bet_value, None

    # Мультисессии 
    async def claim_game(self, game_name: str, user_id: str, guild_id: str) -> Tuple[bool, Optional[Embed]]:
        if not await self._sessions.claim(game_name, user_id, guild_id):
            return False, Embed.error(
                f"У вас уже есть активная игра «{game_name}». Завершите её, чтобы начать новую."
            )
        return True, None

    async def release_game(self, game_name: str, user_id: str, guild_id: str) -> None:
        await self._sessions.release(game_name, user_id, guild_id)

    async def has_active_game(self, game_name: str, user_id: str, guild_id: str) -> bool:
        return await self._sessions.has_active(game_name, user_id, guild_id)

    # Остальное без изменений 
    async def ensure_balance(self, user_id: str, guild_id: str, required_amount: int) -> Tuple[bool, str]:
        if required_amount <= 0:
            return False, "Сумма должна быть положительной"
        balance = await self.economy.get_wallet(user_id, guild_id)
        if balance < required_amount:
            return False, f"Недостаточно средств! Баланс {balance:,} {Emojis.MONEY}"
        return True, ""

    async def validate_transfer(
        self,
        from_user_id: str,
        to_user_id: str,
        guild_id: str,
        amount: int,
        *,
        bot=None,
    ) -> Tuple[bool, str]:
        if from_user_id == to_user_id:
            return False, "Нельзя переводить самому себе"
        if amount <= 0:
            return False, "Сумма должна быть положительной"

        if bot is not None:
            target = await bot.fetch_user(int(to_user_id))
            if target and target.bot:
                return False, "Нельзя переводить ботам"

        await self.economy._ensure_bundle(to_user_id, guild_id)
        ok, message = await self.ensure_balance(from_user_id, guild_id, amount)
        if not ok:
            return False, message
        return True, ""

    @staticmethod
    def parse_amount(amount: Union[str, int]) -> Tuple[bool, int, str]:
        if isinstance(amount, int):
            value = amount
        else:
            amount_str = str(amount).strip()
            if not amount_str:
                return False, 0, "Сумма не может быть пустой"
            if any(symbol in amount_str for symbol in (",", ".")):
                return False, 0, "Сумма должна быть целым числом"
            if amount_str.startswith("-") or (len(amount_str) > 1 and amount_str.startswith("0")):
                return False, 0, "Допускаются только положительные числа без лидирующих нулей"
            if not amount_str.isdigit():
                return False, 0, "Сумма должна содержать только цифры"
            value = int(amount_str)

        if value <= 0:
            return False, 0, "Сумма должна быть больше нуля"
        return True, value, ""

