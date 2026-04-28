from ..tools.Emojis import Emojis
from ..tools.Time import TimeService

import asyncio
from typing import Any, Dict, Optional
from Niludetsu.database import database

class EconomyResult:
    """Результат операции экономии для удобной обработки в match/case."""
    __slots__ = ("status", "message", "data")

    def __init__(self, status: str, message: str = "", data: Optional[Dict] = None):
        self.status = status # 'success', 'error', 'insufficient_funds', 'cooldown'
        self.message = message
        self.data = data or {}

    @property
    def ok(self) -> bool:
        return self.status == "success"

    def __bool__(self) -> bool:
        return self.ok

    def __iter__(self):
        yield self.ok
        yield self.message

class EconomyManager:
    """Менеджер экономики. Динамические настройки из БД + атомарные операции."""

    # Дефолтные значения (если в БД пусто)
    DEFAULT_CONFIG = {
        "cooldowns": {"daily": 1440, "work": 60, "rob": 360, "crime": 120, "slut": 120},
        "cooldown_fields": {"daily": "last_daily", "work": "last_work", "rob": "last_rob", "slut": "last_slut"},
        "rewards": {"work": [120, 260], "daily": [500, 1000]}
    }

    def __init__(self, db=None):
        self.db = db or database
        self.time = TimeService()

    @staticmethod
    def _normalize_account(account: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not account:
            return None
        for field in ("balance", "deposit", "spousal_balance"):
            account[field] = int(account.get(field) or 0)
        return account

    @staticmethod
    def _invalid_amount_result() -> EconomyResult:
        return EconomyResult("error", "Сумма должна быть больше 0")

    async def _store_account(self, user_id: str, guild_id: str, account: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        account = self._normalize_account(account)
        if account:
            await self.db.update_user_cache(str(user_id), str(guild_id), "economy", account)
        return account

    async def _fetch_updated_account(self, query: str, *params: Any) -> Optional[Dict[str, Any]]:
        row = await self.db._neon.fetchrow(query, *params)
        return self._normalize_account(dict(row)) if row else None

    def _schedule_transaction(
        self,
        user_id: str,
        guild_id: str,
        event: str,
        amount: int,
        balance: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not event:
            return
        asyncio.create_task(
            self.db.insert_transaction(
                user_id,
                guild_id,
                event,
                amount,
                balance,
                metadata=metadata,
            )
        )

    async def get_config(self) -> Dict[str, Any]:
        """Получает конфигурацию из настроек БД."""
        return await self.db.get_settings("economy_config", self.DEFAULT_CONFIG)

    async def get_account(self, user_id: str, guild_id: str) -> Dict[str, Any]:
        user_data = await self.db.get_user(str(user_id), str(guild_id))
        return self._normalize_account(user_data["economy"])

    async def add_money(
        self,
        user_id: str,
        guild_id: str,
        amount: int,
        event: str = "",
        share_spousal: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> EconomyResult:
        if amount <= 0: return self._invalid_amount_result()
        
        acc = await self.get_account(user_id, guild_id)
        
        if share_spousal and acc.get("spousal_enabled"):
            share = int(amount * 0.1)
            personal = amount - share
            query = """
                UPDATE public.user_economy 
                SET balance = balance + $3, spousal_balance = spousal_balance + $4, updated_at = now()
                WHERE user_id = $1 AND guild_id = $2
                RETURNING *
            """
            new_acc = await self._fetch_updated_account(query, str(user_id), str(guild_id), personal, share)
            msg = f"Получено **{personal:,}** {Emojis.MONEY} (**{share:,}** {Emojis.MONEY} в семью)"
        else:
            new_acc = await self.db.increment_field(
                "user_economy",
                {"user_id": str(user_id), "guild_id": str(guild_id)},
                "balance",
                amount,
            )
            msg = f"Получено **{amount:,}** {Emojis.MONEY}"

        if new_acc := await self._store_account(user_id, guild_id, new_acc):
            self._schedule_transaction(user_id, guild_id, event, amount, new_acc["balance"], metadata=metadata)
            return EconomyResult("success", msg, data=new_acc)
        
        return EconomyResult("error", "Не удалось обновить баланс")

    async def remove_money(self, user_id: str, guild_id: str, amount: int, event: str = "") -> EconomyResult:
        if amount <= 0: return self._invalid_amount_result()
        
        query = """
            UPDATE public.user_economy 
            SET balance = balance - $3, updated_at = now()
            WHERE user_id = $1 AND guild_id = $2 AND balance >= $3
            RETURNING *
        """
        new_acc = await self._fetch_updated_account(query, str(user_id), str(guild_id), amount)
        
        if new_acc := await self._store_account(user_id, guild_id, new_acc):
            self._schedule_transaction(user_id, guild_id, event, -amount, new_acc["balance"])
            return EconomyResult("success", f"Снято **{amount:,}** {Emojis.MONEY}", data=new_acc)
        
        return EconomyResult("insufficient_funds", "Недостаточно средств")

    async def transfer_money(self, sender_id: str, target_id: str, guild_id: str, amount: int, event: str = "transfer") -> EconomyResult:
        res = await self.remove_money(sender_id, guild_id, amount, event=f"{event}_out")
        if not res:
            return res
        
        add_res = await self.add_money(target_id, guild_id, amount, event=f"{event}_in", share_spousal=False)
        if not add_res:
            await self.add_money(sender_id, guild_id, amount, event=f"{event}_refund", share_spousal=False)
            return add_res

        return EconomyResult("success", f"Переведено **{amount:,}** {Emojis.MONEY}")

    async def deposit_money(self, user_id: str, guild_id: str, amount: int) -> EconomyResult:
        if amount <= 0: return self._invalid_amount_result()
        
        query = """
            UPDATE public.user_economy 
            SET balance = balance - $3, deposit = deposit + $3, updated_at = now()
            WHERE user_id = $1 AND guild_id = $2 AND balance >= $3
            RETURNING *
        """
        new_acc = await self._fetch_updated_account(query, str(user_id), str(guild_id), amount)
        if new_acc := await self._store_account(user_id, guild_id, new_acc):
            return EconomyResult("success", "Деньги внесены на депозит", data=new_acc)
        return EconomyResult("insufficient_funds", "Недостаточно наличных")

    async def withdraw_money(self, user_id: str, guild_id: str, amount: int) -> EconomyResult:
        if amount <= 0: return self._invalid_amount_result()
        
        query = """
            UPDATE public.user_economy 
            SET balance = balance + $3, deposit = deposit - $3, updated_at = now()
            WHERE user_id = $1 AND guild_id = $2 AND deposit >= $3
            RETURNING *
        """
        new_acc = await self._fetch_updated_account(query, str(user_id), str(guild_id), amount)
        if new_acc := await self._store_account(user_id, guild_id, new_acc):
            return EconomyResult("success", "Деньги сняты с депозита", data=new_acc)
        return EconomyResult("insufficient_funds", "Недостаточно средств в банке")

    async def withdraw_spousal(self, user_id: str, guild_id: str, amount: int = None) -> EconomyResult:
        acc = await self.get_account(user_id, guild_id)
        available = acc["spousal_balance"]
        if amount is None: amount = available
        if amount <= 0: return self._invalid_amount_result()
        
        query = """
            UPDATE public.user_economy 
            SET balance = balance + $3, spousal_balance = spousal_balance - $3, updated_at = now()
            WHERE user_id = $1 AND guild_id = $2 AND spousal_balance >= $3
            RETURNING *
        """
        new_acc = await self._fetch_updated_account(query, str(user_id), str(guild_id), amount)
        if new_acc := await self._store_account(user_id, guild_id, new_acc):
            return EconomyResult("success", f"Снято **{amount:,}** {Emojis.MONEY} с семейного счета", data=new_acc)
        return EconomyResult("insufficient_funds", "Недостаточно средств на семейном счету")

    async def check_cooldown(
        self,
        user_id: str,
        guild_id: str,
        command: str,
        *,
        config: Optional[Dict[str, Any]] = None,
        account: Optional[Dict[str, Any]] = None,
    ) -> EconomyResult:
        """Перевіряє кулдаун. Приймає pre-fetched config/account щоб уникнути зайвих DB-запитів."""
        if config is None:
            config = await self.get_config()
        cooldowns = config.get("cooldowns", self.DEFAULT_CONFIG["cooldowns"])

        mins = cooldowns.get(command)
        if not mins:
            return EconomyResult("success")

        if account is None:
            account = await self.get_account(user_id, guild_id)
        cooldown_fields = config.get("cooldown_fields", self.DEFAULT_CONFIG["cooldown_fields"])
        field = cooldown_fields.get(command)
        last_raw = account.get(field) or (account.get("cooldowns") or {}).get(command)

        last_dt = self.time.ensure_datetime(last_raw)
        if not last_dt:
            return EconomyResult("success")

        end = last_dt.add(minutes=mins)
        now = self.time.now()
        if end > now:
            return EconomyResult("cooldown", self.time.format_duration(int((end - now).total_seconds())))
        return EconomyResult("success")

    async def update_cooldown(
        self,
        user_id: str,
        guild_id: str,
        command: str,
        *,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Оновлює кулдаун. Приймає pre-fetched config щоб уникнути зайвого DB-запиту."""
        now = self.time.now()
        if config is None:
            config = await self.get_config()
        cooldown_fields = config.get("cooldown_fields", self.DEFAULT_CONFIG["cooldown_fields"])
        field = cooldown_fields.get(command)

        if field:
            new_acc = await self.db.update_record(
                "user_economy",
                {"user_id": str(user_id), "guild_id": str(guild_id)},
                {field: now},
            )
        else:
            query = """
                UPDATE public.user_economy
                SET cooldowns = jsonb_set(COALESCE(cooldowns, '{}'::jsonb), ARRAY[$3], $4::jsonb),
                    updated_at = now()
                WHERE user_id = $1 AND guild_id = $2
                RETURNING *
            """
            now_json = f'"{now.to_iso8601_string()}"'
            new_acc = await self._fetch_updated_account(query, str(user_id), str(guild_id), command, now_json)

        await self._store_account(user_id, guild_id, new_acc)

    async def check_and_update_cooldown(
        self,
        user_id: str,
        guild_id: str,
        command: str,
    ) -> tuple[EconomyResult, Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        Перевіряє і оновлює кулдаун за один DB-цикл.
        Повертає (result, config, account) — можна використовувати далі без зайвих запитів.
        """
        config = await self.get_config()
        account = await self.get_account(user_id, guild_id)
        result = await self.check_cooldown(user_id, guild_id, command, config=config, account=account)
        if result.ok:
            await self.update_cooldown(user_id, guild_id, command, config=config)
        return result, config, account
