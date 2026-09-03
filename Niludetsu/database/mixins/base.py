from __future__ import annotations

import json
import re
import time
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Optional

import asyncpg
from loguru import logger

from ..pool import NeonPool
from ..query import QueryBuilder


_COL_RE = re.compile(r"^[a-z_][a-z0-9_]*$", re.IGNORECASE)
_TABLE_RE = re.compile(r"^[a-z_][a-z0-9_]*$", re.IGNORECASE)


def _safe_col(name: str) -> str:
    if not _COL_RE.match(name):
        raise ValueError(f"Invalid column name: {name!r}")
    return name


def _safe_table(name: str) -> str:
    if not _TABLE_RE.match(name):
        raise ValueError(f"Invalid table name: {name!r}")
    return name


class BaseMixin:
    def __init__(self):
        self._neon = NeonPool()
        self._settings_cache: dict[str, tuple[Any, float]] = {}

    async def _get_pool(self) -> asyncpg.Pool:
        return await self._neon.get_pool()

    async def close(self) -> None:
        await self._neon.close()

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[asyncpg.Connection]:
        async with self._neon.transaction() as conn:
            yield conn


    async def get_row(self, table: str, **conditions: Any) -> Optional[dict[str, Any]]:
        keys = list(conditions.keys())
        where = " AND ".join(f'"{_safe_col(k)}" = ${i+1}' for i, k in enumerate(keys))
        query = f'SELECT * FROM public."{_safe_table(table)}" WHERE {where} LIMIT 1'
        row = await self._neon.fetchrow(query, *conditions.values())
        return dict(row) if row else None

    async def get_rows(
        self,
        table: str,
        *,
        limit: int | None = None,
        order: str | None = None,
        ascending: bool = True,
        **conditions: Any,
    ) -> list[dict[str, Any]]:
        params: list[Any] = []
        idx = 1

        if conditions:
            keys = list(conditions.keys())
            where = " WHERE " + " AND ".join(f'"{_safe_col(k)}" = ${i+idx}' for i, k in enumerate(keys))
            params.extend(conditions.values())
            idx += len(keys)
        else:
            where = ""

        query = f'SELECT * FROM public."{_safe_table(table)}"{where}'

        if order:
            direction = "ASC" if ascending else "DESC"
            query += f' ORDER BY "{_safe_col(order)}" {direction}'

        if limit is not None:
            query += f" LIMIT ${idx}"
            params.append(limit)

        rows = await self._neon.fetch(query, *params)
        return [dict(r) for r in rows]

    async def insert(self, table: str, values: dict[str, Any]) -> Optional[dict[str, Any]]:
        cols = list(values.keys())
        placeholders = ", ".join(f"${i+1}" for i in range(len(cols)))
        col_names = ", ".join(f'"{_safe_col(c)}"' for c in cols)
        query = f'INSERT INTO public."{_safe_table(table)}" ({col_names}) VALUES ({placeholders}) RETURNING *'
        row = await self._neon.fetchrow(query, *values.values())
        return dict(row) if row else None

    async def update_record(
        self,
        table: str,
        where: dict[str, Any],
        values: dict[str, Any],
        *,
        json_fields: Optional[list[str]] = None,
        ensure_if_missing: bool = False,
        ensure_params: Optional[dict[str, Any]] = None,
    ) -> Optional[dict[str, Any]]:
        if json_fields:
            current = await self.get_row(table, **where)
            if current:
                for field in json_fields:
                    if field in values and isinstance(values[field], dict):
                        base = current.get(field) or {}
                        if isinstance(base, str):
                            try:
                                base = json.loads(base)
                            except Exception:
                                base = {}
                        
                        if isinstance(base, dict):
                            base.update(values[field])
                            values[field] = base

        set_cols = list(values.keys())
        where_keys = list(where.keys())

        set_clause = ", ".join(f'"{_safe_col(k)}" = ${i+1}' for i, k in enumerate(set_cols))
        where_clause = " AND ".join(f'"{_safe_col(k)}" = ${i+1+len(set_cols)}' for i, k in enumerate(where_keys))

        query = f'UPDATE public."{_safe_table(table)}" SET {set_clause} WHERE {where_clause} RETURNING *'
        row = await self._neon.fetchrow(query, *values.values(), *where.values())

        if row:
            return dict(row)

        if ensure_if_missing:
            params = {**where, **(ensure_params or {}), **values}
            return await self.ensure_record(table, **params)
        return None

    async def delete(self, table: str, **conditions: Any) -> int:
        keys = list(conditions.keys())
        where = " AND ".join(f'"{_safe_col(k)}" = ${i+1}' for i, k in enumerate(keys))
        query = f'DELETE FROM public."{_safe_table(table)}" WHERE {where}'
        res = await self._neon.execute(query, *conditions.values())
        return int(res.split(" ")[1])

    async def upsert(
        self,
        table: str,
        payload: dict[str, Any] | list[dict[str, Any]],
        on_conflict: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        if isinstance(payload, dict):
            payload = [payload]
        if not payload:
            return []

        cols = list(payload[0].keys())
        col_names = ", ".join(f'"{_safe_col(c)}"' for c in cols)

        conflict_clause = ""
        if on_conflict:
            conflict_keys = [k.strip() for k in on_conflict.split(",")]
            update_cols = ", ".join(
                f'"{_safe_col(c)}" = EXCLUDED."{_safe_col(c)}"' for c in cols if c not in conflict_keys
            )
            if update_cols:
                conflict_clause = f" ON CONFLICT ({on_conflict}) DO UPDATE SET {update_cols}"
            else:
                first_key = _safe_col(conflict_keys[0])
                conflict_clause = f' ON CONFLICT ({on_conflict}) DO UPDATE SET "{first_key}" = EXCLUDED."{first_key}"'

        values_sql: list[str] = []
        params: list[Any] = []
        param_idx = 1

        for item in payload:
            placeholders = []
            for col in cols:
                placeholders.append(f"${param_idx}")
                params.append(item.get(col))
                param_idx += 1
            values_sql.append(f"({', '.join(placeholders)})")

        query = (
            f'INSERT INTO public."{_safe_table(table)}" ({col_names}) VALUES '
            f"{', '.join(values_sql)}{conflict_clause} RETURNING *"
        )
        rows = await self._neon.fetch(query, *params)
        return [dict(row) for row in rows]

    async def increment_field(
        self, table: str, where: dict[str, Any], field: str, amount: int
    ) -> Optional[dict[str, Any]]:
        where_keys = list(where.keys())
        where_clause = " AND ".join(f'"{_safe_col(k)}" = ${i+2}' for i, k in enumerate(where_keys))
        query = f'UPDATE public."{_safe_table(table)}" SET "{_safe_col(field)}" = "{_safe_col(field)}" + $1 WHERE {where_clause} RETURNING *'
        row = await self._neon.fetchrow(query, amount, *where.values())
        return dict(row) if row else None


    async def get_settings(self, key: str, default: Any = None) -> Any:
        cached = self._settings_cache.get(key)
        if cached and (time.time() - cached[1] < 60):
            return cached[0]

        val = await self._neon.fetchval("SELECT value FROM public.settings WHERE key = $1", key)
        result = json.loads(val) if isinstance(val, str) else (val if val is not None else default)

        self._settings_cache[key] = (result, time.time())
        return result

    async def set_settings(self, key: str, value: Any) -> None:
        await self._neon.execute(
            "INSERT INTO public.settings (key, value) VALUES ($1, $2) "
            "ON CONFLICT (key) DO UPDATE SET value = $2, updated_at = now()",
            key,
            value,
        )
        self._settings_cache[key] = (value, time.time())


    async def where(
        self,
        table: str,
        *,
        filters: list[dict[str, Any]] | None = None,
        columns: list[str] | None = None,
        order: list[dict[str, Any]] | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[dict[str, Any]]:
        qb = QueryBuilder(table)
        if filters:
            qb.filter(filters)
        if columns:
            qb.select(columns)
        if order:
            qb.order_by(order)
        if limit is not None:
            qb.limit(limit)
        if offset is not None:
            qb.offset(offset)

        sql, params = qb.build()
        rows = await self._neon.fetch(sql, *params)
        return [dict(r) for r in rows]
