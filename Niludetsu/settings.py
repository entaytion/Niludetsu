from __future__ import annotations

import json
import time
from typing import Any

from loguru import logger


class Settings:

    _CACHE_TTL = 300

    def __init__(self) -> None:
        self._cache: dict[str, Any] = {}
        self._loaded_at: float = 0.0
        self._db = None


    def _get_db(self):
        if self._db is None:
            from .database import database
            self._db = database
        return self._db

    def _fallback(self, key: str) -> Any:
        try:
            from . import config
            return getattr(config, key, None)
        except Exception:
            return None


    async def load(self) -> None:
        db = self._get_db()
        try:
            rows = await db.get_rows("settings")
            new_cache: dict[str, Any] = {}
            for row in rows:
                raw = row.get("value")
                if isinstance(raw, str):
                    try:
                        raw = json.loads(raw)
                    except Exception:
                        pass
                new_cache[row["key"]] = raw
            self._cache = new_cache
            self._loaded_at = time.time()
            logger.info("⚙️ Settings завантажено з БД ({} ключів)", len(self._cache))
        except Exception as e:
            logger.warning("⚠️ Не вдалося завантажити settings з БД: {}. Fallback на config.py", e)

    async def refresh(self) -> None:
        self._cache.clear()
        self._loaded_at = 0.0
        await self.load()

    async def get(self, key: str, default: Any = None) -> Any:
        if time.time() - self._loaded_at > self._CACHE_TTL:
            await self.load()
        value = self._cache.get(key)
        if value is None:
            value = self._fallback(key)
        return value if value is not None else default

    async def set(self, key: str, value: Any) -> None:
        db = self._get_db()
        await db.set_settings(key, value if not isinstance(value, (dict, list)) else json.dumps(value))
        self._cache[key] = value
        logger.debug("⚙️ Settings.set: {} = {}", key, value)


    def __getattr__(self, key: str) -> Any:
        if key.startswith("_"):
            raise AttributeError(key)
        value = self._cache.get(key)
        if value is None:
            value = self._fallback(key)
        return value

    def __setattr__(self, key: str, value: Any) -> None:
        if key.startswith("_") or key in ("_cache", "_loaded_at", "_db"):
            super().__setattr__(key, value)
        else:
            self._cache[key] = value


settings = Settings()
