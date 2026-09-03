from __future__ import annotations

from typing import Any

from .bot import get_bot, get_config_manager


class WebDatabase:

    async def is_premium(self, guild_id: str) -> bool:
        cm = get_config_manager()
        if cm and cm._loaded:
            return cm.is_premium(int(guild_id))
        try:
            bot = get_bot()
            row = await bot.db._neon.fetchrow(
                "SELECT 1 FROM public.premium_guilds WHERE guild_id = $1 AND expires_at > now()",
                str(guild_id),
            )
            return row is not None
        except Exception:
            return False

    async def get_user(self, user_id: str, guild_id: str) -> dict | None:
        bot = get_bot()
        if not bot:
            return None
        try:
            return await bot.db.get_user(str(user_id), str(guild_id))
        except Exception:
            return None

    async def get_guild_settings(self, guild_id: str) -> dict[str, dict[str, Any]]:
        cm = get_config_manager()
        if cm and cm._loaded:
            return cm._custom_configs.get(int(guild_id), {})
        try:
            bot = get_bot()
            rows = await bot.db._neon.fetch(
                "SELECT module, key, value FROM public.custom_messages WHERE guild_id = $1",
                str(guild_id),
            )
            result: dict[str, dict[str, Any]] = {}
            for row in rows:
                module = row["module"]
                key = row["key"]
                val = row["value"]
                result.setdefault(module, {})[key] = val
            return result
        except Exception:
            return {}

    async def set_guild_setting(
        self, guild_id: str, module: str, key: str, value: Any
    ) -> bool:
        cm = get_config_manager()
        if cm:
            try:
                await cm.set_custom_value(int(guild_id), module, key, value)
                return True
            except Exception:
                return False
        bot = get_bot()
        if not bot:
            return False
        try:
            await bot.db._neon.execute(
                "INSERT INTO public.custom_messages (guild_id, module, key, value, updated_at) "
                "VALUES ($1, $2, $3, $4, now()) "
                "ON CONFLICT (guild_id, module, key) "
                "DO UPDATE SET value = $4, updated_at = now()",
                str(guild_id), module, key, value,
            )
            return True
        except Exception:
            return False


db = WebDatabase()
