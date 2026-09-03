from __future__ import annotations

import asyncio
import json
import os
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

import asyncpg
from dotenv import load_dotenv
from loguru import logger

from .errors import DatabaseConnectionError, RetryExhaustedError

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

_RETRYABLE = (
    asyncpg.ConnectionDoesNotExistError,
    asyncpg.InterfaceError,
    asyncpg.InternalClientError,
    asyncpg.TooManyConnectionsError,
    ConnectionResetError,
    OSError,
)

_MAX_RETRIES = 3
_BACKOFF = (0.5, 1.0, 2.0)


class NeonPool:
    def __init__(
        self,
        dsn: str | None = None,
        *,
        min_size: int = 2,
        max_size: int = 10,
        max_inactive_connection_lifetime: float = 180,
        command_timeout: float = 30,
        statement_cache_size: int = 0,
    ):
        self._dsn = dsn or DATABASE_URL
        self._min_size = min_size
        self._max_size = max_size
        self._max_inactive = max_inactive_connection_lifetime
        self._command_timeout = command_timeout
        self._statement_cache_size = statement_cache_size
        self._pool: asyncpg.Pool | None = None
        self._lock = asyncio.Lock()

    async def _create_pool(self) -> asyncpg.Pool:
        async def init(conn):
            await conn.set_type_codec(
                'jsonb',
                encoder=json.dumps,
                decoder=json.loads,
                schema='pg_catalog'
            )
            await conn.set_type_codec(
                'json',
                encoder=json.dumps,
                decoder=json.loads,
                schema='pg_catalog'
            )

        return await asyncpg.create_pool(
            self._dsn,
            min_size=self._min_size,
            max_size=self._max_size,
            max_inactive_connection_lifetime=self._max_inactive,
            command_timeout=self._command_timeout,
            statement_cache_size=self._statement_cache_size,
            init=init
        )

    async def get_pool(self) -> asyncpg.Pool:
        if self._pool and not self._pool._closed:
            return self._pool
        async with self._lock:
            if self._pool and not self._pool._closed:
                return self._pool
            try:
                self._pool = await self._create_pool()
                logger.success("Connected to Neon Database Pool")
            except Exception as e:
                logger.error(f"Failed to create Neon pool: {e}")
                raise DatabaseConnectionError(str(e)) from e
            return self._pool

    async def _ensure_healthy_pool(self) -> asyncpg.Pool:
        pool = await self.get_pool()
        try:
            async with pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return pool
        except _RETRYABLE:
            logger.warning("Pool health check failed, recreating pool")
            await self._recreate()
            return await self.get_pool()

    async def _recreate(self) -> None:
        async with self._lock:
            if self._pool and not self._pool._closed:
                try:
                    await asyncio.wait_for(self._pool.close(), timeout=5)
                except Exception:
                    self._pool.terminate()
            self._pool = await self._create_pool()
            logger.info("Neon pool recreated")

    async def execute(self, query: str, *args: Any, timeout: float | None = None) -> str:
        return await self._retry(lambda conn: conn.execute(query, *args, timeout=timeout))

    async def fetch(self, query: str, *args: Any, timeout: float | None = None) -> list[asyncpg.Record]:
        return await self._retry(lambda conn: conn.fetch(query, *args, timeout=timeout))

    async def fetchrow(self, query: str, *args: Any, timeout: float | None = None) -> asyncpg.Record | None:
        return await self._retry(lambda conn: conn.fetchrow(query, *args, timeout=timeout))

    async def fetchval(self, query: str, *args: Any, timeout: float | None = None) -> Any:
        return await self._retry(lambda conn: conn.fetchval(query, *args, timeout=timeout))

    async def _retry(self, operation):
        last_error = None
        for attempt in range(_MAX_RETRIES):
            pool = await self.get_pool()
            try:
                async with pool.acquire() as conn:
                    return await operation(conn)
            except _RETRYABLE as e:
                last_error = e
                delay = _BACKOFF[attempt] if attempt < len(_BACKOFF) else _BACKOFF[-1]
                logger.warning(f"Database retry {attempt + 1}/{_MAX_RETRIES}: {type(e).__name__}: {e}")
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(delay)
                    if attempt >= 1:
                        await self._recreate()

        raise RetryExhaustedError(f"All {_MAX_RETRIES} retries exhausted: {last_error}") from last_error

    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[asyncpg.Connection]:
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            yield conn

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[asyncpg.Connection]:
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                yield conn

    async def close(self) -> None:
        if self._pool and not self._pool._closed:
            await self._pool.close()
            logger.info("Neon pool closed")
        self._pool = None
