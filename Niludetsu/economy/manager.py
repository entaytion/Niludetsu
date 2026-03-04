from Niludetsu.database.supabase_database import SupabaseDatabase
from Niludetsu.tools.Embed import Embed
from Niludetsu.tools.Emojis import Emojis
from Niludetsu.tools.Time import TimeService
from typing import Any, Dict, Optional, Tuple

class EconomyManager:
    """Единая точка входа: балансы, депозиты, семейные счета, кулдауны."""

    # КОНСТАНТЫ КУЛДАУНОВ (в минутах)
    COOLDOWNS = {
        "daily": 24 * 60,      # 24 часа
        "work": 60,            # 1 час
        "rob": 6 * 60,         # 6 часов
        "crime": 2 * 60,       # 2 часа
        "slut": 2 * 60,        # 2 часа
    }

    # Маппинг команда -> поле в БД
    COOLDOWN_FIELDS = {
        "daily": "last_daily",
        "work": "last_work",
        "rob": "last_rob",
        "slut": "last_slut",
        # Для остальных команд используем cooldowns (jsonb)
    }

    def __init__(self, db: SupabaseDatabase):
        self.db = db
        self.time = TimeService()

    # 1. Доступ к данным
    async def _ensure_bundle(self, user_id: str, guild_id: str) -> Dict[str, Any]:
        return await self.db.ensure_user(str(user_id), str(guild_id))

    async def _get_economy(self, user_id: str, guild_id: str) -> Dict[str, Any]:
        bundle = await self._ensure_bundle(user_id, guild_id)
        economy: Dict[str, Any] = bundle.get("economy") or {}

        economy.setdefault("balance", 0)
        economy.setdefault("deposit", 0)
        economy.setdefault("spousal_balance", 0)
        economy.setdefault("spousal_enabled", False)
        economy.setdefault("last_daily", None)
        economy.setdefault("last_work", None)
        economy.setdefault("last_rob", None)
        economy.setdefault("last_slut", None)
        economy.setdefault("cooldowns", {})

        economy["balance"] = int(economy["balance"] or 0)
        economy["deposit"] = int(economy["deposit"] or 0)
        economy["spousal_balance"] = int(economy["spousal_balance"] or 0)

        return economy

    async def _update_economy(
        self,
        user_id: str,
        guild_id: str,
        *,
        balance: Optional[int] = None,
        deposit: Optional[int] = None,
        spousal_balance: Optional[int] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        if balance is not None:
            payload["balance"] = int(balance)
        if deposit is not None:
            payload["deposit"] = int(deposit)
        if spousal_balance is not None:
            payload["spousal_balance"] = int(spousal_balance)
        if extra:
            payload.update(extra)

        if not payload:
            return await self._get_economy(user_id, guild_id)

        updated = await self.db.update_economy(
            str(user_id),
            str(guild_id),
            payload,
        )
        return updated or await self._get_economy(user_id, guild_id)

    # 2. Получение данных
    async def get_account(self, user_id: str, guild_id: str) -> Dict[str, Any]:
        return await self._get_economy(user_id, guild_id)

    async def get_wallet(self, user_id: str, guild_id: str) -> int:
        economy = await self._get_economy(user_id, guild_id)
        return int(economy.get("balance", 0))

    async def get_bank(self, user_id: str, guild_id: str) -> int:
        economy = await self._get_economy(user_id, guild_id)
        return int(economy.get("deposit", 0))

    async def get_spousal_balance(self, user_id: str, guild_id: str) -> int:
        economy = await self._get_economy(user_id, guild_id)
        return int(economy.get("spousal_balance", 0))

    # 3. Операции с деньгами
    async def add_money(
        self,
        user_id: str,
        guild_id: str,
        amount: int,
        *,
        share_spousal: bool = True,
    ) -> Tuple[bool, str]:
        if amount <= 0:
            return False, "Сумма должна быть положительной"

        economy = await self._get_economy(user_id, guild_id)
        wallet = int(economy["balance"])
        spousal_enabled = bool(economy.get("spousal_enabled"))

        spousal_balance_raw = economy.get("spousal_balance")
        spousal_balance = int(spousal_balance_raw) if spousal_balance_raw is not None else 0

        if share_spousal and spousal_enabled:
            share = int(amount * 0.1)
            personal_amount = amount - share

            await self._update_economy(
                user_id,
                guild_id,
                balance=wallet + personal_amount,
                spousal_balance=spousal_balance + share,
            )

            message = (
                f"{personal_amount:,} {Emojis.MONEY} на личный счёт | "
                f"{share:,} {Emojis.MONEY} в семейный бюджет"
            )
            return True, message

        await self._update_economy(
            user_id,
            guild_id,
            balance=wallet + amount,
        )
        return True, f"{amount:,} {Emojis.MONEY}"

    async def remove_money(self, user_id: str, guild_id: str, amount: int) -> Tuple[bool, str]:
        if amount <= 0:
            return False, "Сумма должна быть положительной"

        balance = await self.get_wallet(user_id, guild_id)
        if balance < amount:
            return False, "Недостаточно средств"

        await self._update_economy(
            user_id,
            guild_id,
            balance=balance - amount,
        )
        return True, f"Списано {amount:,} {Emojis.MONEY}"

    async def transfer_money(self, from_user_id: str, to_user_id: str, guild_id: str, amount: int) -> Tuple[bool, str]:
        if amount <= 0:
            return False, "Сумма должна быть положительной"
        if from_user_id == to_user_id:
            return False, "Нельзя переводить самому себе"

        sender_balance = await self.get_wallet(from_user_id, guild_id)
        if sender_balance < amount:
            return False, "Недостаточно средств"

        receiver_balance = await self.get_wallet(to_user_id, guild_id)

        await self._update_economy(
            from_user_id,
            guild_id,
            balance=sender_balance - amount,
        )
        await self._update_economy(
            to_user_id,
            guild_id,
            balance=receiver_balance + amount,
        )
        return True, f"Перевод {amount:,} {Emojis.MONEY} выполнен"

    # 4. Операции с банком и семейным счётом
    async def deposit_money(self, user_id: str, guild_id: str, amount: int) -> Tuple[bool, str]:
        balance = await self.get_wallet(user_id, guild_id)
        if amount <= 0 or balance < amount:
            return False, "Недостаточно средств"

        bank = await self.get_bank(user_id, guild_id)
        await self._update_economy(
            user_id,
            guild_id,
            balance=balance - amount,
            deposit=bank + amount,
        )
        return True, f"Внесено {amount:,} {Emojis.MONEY} в банк"

    async def withdraw_money(self, user_id: str, guild_id: str, amount: int) -> Tuple[bool, str]:
        bank = await self.get_bank(user_id, guild_id)
        if amount <= 0 or bank < amount:
            return False, "Недостаточно средств на депозите"

        balance = await self.get_wallet(user_id, guild_id)
        await self._update_economy(
            user_id,
            guild_id,
            balance=balance + amount,
            deposit=bank - amount,
        )
        return True, f"Снято {amount:,} {Emojis.MONEY} с депозита"

    async def withdraw_spousal(self, user_id: str, guild_id: str, amount: Optional[int]) -> Tuple[bool, Embed]:
        economy = await self._get_economy(user_id, guild_id)
        family_balance = int(economy.get("spousal_balance", 0))

        if family_balance <= 0:
            return False, Embed.error("На семейном счёте нет средств")

        amount_to_withdraw = family_balance if amount is None else int(amount)
        if amount_to_withdraw <= 0:
            return False, Embed.error("Сумма должна быть положительной")
        if family_balance < amount_to_withdraw:
            return False, Embed.error(f"Недостаточно средств: доступно {family_balance:,} {Emojis.MONEY}")

        await self._update_economy(
            user_id,
            guild_id,
            balance=int(economy["balance"]) + amount_to_withdraw,
            spousal_balance=family_balance - amount_to_withdraw,
        )

        return True, Embed.success(f"Снято {amount_to_withdraw:,} {Emojis.MONEY} с семейного счёта")

    # 5. КУЛДАУНЫ (новая логика вместо Cooldown.py)
    async def check_cooldown(
        self,
        user_id: str,
        guild_id: str,
        command: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Проверяет кулдаун команды экономики.

        Returns:
            (can_use, error_message)
            - can_use: True если можно использовать
            - error_message: Сообщение об ошибке (если кулдаун активен)
        """
        cooldown_minutes = self.COOLDOWNS.get(command)
        if not cooldown_minutes:
            return True, None

        economy = await self._get_economy(user_id, guild_id)
        field = self.COOLDOWN_FIELDS.get(command)

        # Если есть отдельное поле (last_daily, last_work, last_rob)
        if field:
            last_used_raw = economy.get(field)
        else:
            # Иначе проверяем в cooldowns (jsonb)
            cooldowns = economy.get("cooldowns") or {}
            last_used_raw = cooldowns.get(command)

        # Обрабатываем timestamp (может быть int/float или ISO string)
        if isinstance(last_used_raw, (int, float)):
            last_used = self.time.from_timestamp(last_used_raw)
        else:
            last_used = self.time.ensure_datetime(last_used_raw)

        if not last_used:
            return True, None

        now = self.time.now()
        cooldown_end = last_used.add(minutes=cooldown_minutes)

        if cooldown_end > now:
            remaining = int((cooldown_end - now).total_seconds())
            pretty = self.time.format_duration(remaining)
            return False, f"Подождите ещё **{pretty}**"

        return True, None

    async def update_cooldown(
        self,
        user_id: str,
        guild_id: str,
        command: str
    ) -> None:
        """Обновляет время последнего использования команды"""
        now_iso = self.time.now().to_iso8601_string()
        field = self.COOLDOWN_FIELDS.get(command)

        if field:
            # Обновляем отдельное поле (last_daily, last_work, last_rob)
            await self._update_economy(
                user_id,
                guild_id,
                extra={field: now_iso}
            )
        else:
            # Обновляем в cooldowns (jsonb)
            economy = await self._get_economy(user_id, guild_id)
            cooldowns = dict(economy.get("cooldowns") or {})
            cooldowns[command] = now_iso
            await self._update_economy(
                user_id,
                guild_id,
                extra={"cooldowns": cooldowns}
            )

    # 6. Форматирование
    @staticmethod
    def format_money(value: int) -> str:
        return f"**``{value:,}``** {Emojis.MONEY}"

    # 7. Информация о доступных наградах
    async def get_rewards_info(self, user_id: str, guild_id: str) -> str:
        """Возвращает информацию о доступных наградах и их статусе"""
        rewards = []
        
        # Подработка /work
        can_work, work_msg = await self.check_cooldown(user_id, guild_id, "work")
        if can_work:
            rewards.append("- Работать **``/work``** — доступно")
        else:
            rewards.append(f"- Работать **``/work``** — {work_msg}")
        
        # Ежедневный бонус /daily (timely)
        can_daily, daily_msg = await self.check_cooldown(user_id, guild_id, "daily")
        if can_daily:
            rewards.append("- Ежедневный бонус **``/daily``** — доступно")
        else:
            rewards.append(f"- Ежедневный бонус **``/daily``** — {daily_msg}")
        
        # Половая жизнь /slut
        can_daily, daily_msg = await self.check_cooldown(user_id, guild_id, "slut")
        if can_daily:
            rewards.append("- Половая жизнь **``/slut``** — доступно")
        else:
            rewards.append(f"- Половая жизнь **``/slut``** — {daily_msg}")
        return "\n".join(rewards)

