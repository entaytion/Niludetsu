from __future__ import annotations

import json
from typing import Any, Optional

from .base import BaseMixin


class EconomyMixin(BaseMixin):
    async def update_economy(
        self,
        user_id: str,
        guild_id: str,
        values: dict[str, Any],
        *,
        json_fields: Optional[list[str]] = None,
    ) -> Optional[dict[str, Any]]:
        if json_fields is None:
            json_fields = ["cooldowns"]

        where = {"user_id": str(user_id), "guild_id": str(guild_id)}
        return await self.update_record(
            "user_economy",
            where,
            values,
            json_fields=json_fields,
            ensure_if_missing=True,
            ensure_params=where,
        )

    async def fetch_inventory_items(self, user_id: str, guild_id: str) -> list[dict[str, Any]]:
        return await self.get_rows("user_inventory", user_id=str(user_id), guild_id=str(guild_id))

    async def ensure_inventory_item(
        self, user_id: str, guild_id: str, item_key: str, **kwargs: Any
    ) -> dict[str, Any]:
        return await self.ensure_record(
            "user_inventory", user_id=user_id, guild_id=guild_id, item_key=item_key, **kwargs
        )

    async def delete_inventory_item(self, user_id: str, guild_id: str, item_key: str) -> int:
        return await self.delete(
            "user_inventory", user_id=str(user_id), guild_id=str(guild_id), item_key=str(item_key)
        )

    async def insert_transaction(
        self,
        user_id: str,
        guild_id: str,
        event: str,
        amount: int,
        balance_after: int,
        **kwargs: Any,
    ) -> Optional[dict[str, Any]]:
        payload = {
            "user_id": str(user_id),
            "guild_id": str(guild_id),
            "event": event,
            "amount": amount,
            "balance_after": balance_after,
            "related_user_id": str(kwargs["related_user_id"]) if kwargs.get("related_user_id") else None,
            "metadata": kwargs.get("metadata") or {},
        }
        return await self.insert("user_transactions", payload)

    async def get_transactions(
        self,
        user_id: str,
        guild_id: str,
        limit: int = 10,
        offset: int = 0,
        events: list[str] | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        where_parts = ["user_id = $1", "guild_id = $2"]
        params: list[Any] = [str(user_id), str(guild_id)]

        if events:
            where_parts.append("event = ANY($3)")
            params.append(events)

        where_clause = " WHERE " + " AND ".join(where_parts)

        count = await self._neon.fetchval(
            f"SELECT COUNT(*) FROM public.user_transactions {where_clause}", *params
        )

        query = f"""
            SELECT * FROM public.user_transactions
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ${len(params)+1} OFFSET ${len(params)+2}
        """
        rows = await self._neon.fetch(query, *params, limit, offset)
        return [dict(r) for r in rows], count or 0
