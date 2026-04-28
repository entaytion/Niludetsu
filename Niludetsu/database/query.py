from __future__ import annotations

from typing import Any


_OP_MAP = {
    "eq": "=",
    "neq": "!=",
    "gt": ">",
    "gte": ">=",
    "lt": "<",
    "lte": "<=",
    "like": "LIKE",
    "ilike": "ILIKE",
}


class QueryBuilder:
    __slots__ = ("_table", "_filters", "_columns", "_order", "_limit", "_offset")

    def __init__(self, table: str):
        self._table = table
        self._filters: list[dict[str, Any]] = []
        self._columns: list[str] | None = None
        self._order: list[dict[str, Any]] | None = None
        self._limit: int | None = None
        self._offset: int | None = None

    def select(self, columns: list[str]) -> QueryBuilder:
        self._columns = columns
        return self

    def filter(self, filters: list[dict[str, Any]]) -> QueryBuilder:
        self._filters = filters
        return self

    def order_by(self, order: list[dict[str, Any]]) -> QueryBuilder:
        self._order = order
        return self

    def limit(self, n: int) -> QueryBuilder:
        self._limit = n
        return self

    def offset(self, n: int) -> QueryBuilder:
        self._offset = n
        return self

    def build(self) -> tuple[str, list[Any]]:
        cols = ", ".join(f'"{c}"' for c in self._columns) if self._columns else "*"
        sql = f'SELECT {cols} FROM public."{self._table}"'

        params: list[Any] = []
        idx = 1

        if self._filters:
            clauses = []
            for f in self._filters:
                col = f["column"]
                op = f.get("op", "eq")
                val = f.get("value")

                if op == "is":
                    if val is None:
                        clauses.append(f'"{col}" IS NULL')
                    else:
                        clauses.append(f'"{col}" IS NOT NULL')
                elif op == "in":
                    clauses.append(f'"{col}" = ANY(${idx})')
                    params.append(val)
                    idx += 1
                else:
                    sql_op = _OP_MAP.get(op, "=")
                    clauses.append(f'"{col}" {sql_op} ${idx}')
                    params.append(val)
                    idx += 1

            sql += " WHERE " + " AND ".join(clauses)

        if self._order:
            order_parts = []
            for o in self._order:
                direction = "ASC" if o.get("ascending", True) else "DESC"
                order_parts.append(f'"{o["column"]}" {direction}')
            sql += " ORDER BY " + ", ".join(order_parts)

        if self._limit is not None:
            sql += f" LIMIT ${idx}"
            params.append(self._limit)
            idx += 1

        if self._offset is not None:
            sql += f" OFFSET ${idx}"
            params.append(self._offset)
            idx += 1

        return sql, params
