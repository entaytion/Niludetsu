import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from Niludetsu.database.database import database

class ConfigManager:
    def __init__(self, bot):
        self.bot = bot
        self._custom_messages: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self._premium_guilds: Dict[str, Optional[datetime]] = {}
        self._loop_task = None

    async def load_all(self):
        try:
            rows = await database._neon.fetch(
                "SELECT guild_id, module, key, value FROM public.custom_messages"
            )
            self._custom_messages.clear()
            for row in rows:
                gid = str(row["guild_id"])
                module = row["module"]
                key = row["key"]
                val = row["value"]
                self._custom_messages.setdefault(gid, {}).setdefault(module, {})[key] = val

            prem_rows = await database._neon.fetch(
                "SELECT guild_id, expires_at FROM public.premium_guilds"
            )
            self._premium_guilds.clear()
            for row in prem_rows:
                gid = str(row["guild_id"])
                self._premium_guilds[gid] = row["expires_at"]
        except Exception as e:
            print(f"[ConfigManager] Помилка завантаження конфігу: {e}")

        if self._loop_task is None and self.bot and self.bot.loop:
            self._loop_task = self.bot.loop.create_task(self._sync_loop())

    async def _sync_loop(self):
        while True:
            await asyncio.sleep(60)
            try:
                await self.load_all()
            except Exception:
                pass

    def is_premium(self, guild_id: Any) -> bool:
        gid = str(guild_id)
        if gid not in self._premium_guilds:
            return False
        expires_at = self._premium_guilds[gid]
        if expires_at is None:
            return True
        now = datetime.now(timezone.utc)
        return expires_at > now

    def get_custom_embed(self, guild_id: Any, module: str, key: str, default_embed_data: dict, **kwargs) -> dict:
        gid = str(guild_id)
        if not self.is_premium(gid):
            return default_embed_data

        custom = self._custom_messages.get(gid, {}).get(module, {}).get(key)
        if not custom:
            return default_embed_data

        result = json.loads(json.dumps(custom))
        
        def format_value(val: Any) -> Any:
            if isinstance(val, str):
                for k, v in kwargs.items():
                    val = val.replace(f"{{{k}}}", str(v))
                return val
            elif isinstance(val, dict):
                return {k: format_value(v) for k, v in val.items()}
            elif isinstance(val, list):
                return [format_value(v) for v in val]
            return val

        return format_value(result)

    def get_custom_text(self, guild_id: Any, module: str, key: str, default_text: str, **kwargs) -> str:
        gid = str(guild_id)
        if not self.is_premium(gid):
            return default_text.format(**kwargs) if kwargs else default_text

        custom = self._custom_messages.get(gid, {}).get(module, {}).get(key)
        if not custom or not isinstance(custom, str):
            return default_text.format(**kwargs) if kwargs else default_text

        for k, v in kwargs.items():
            custom = custom.replace(f"{{{k}}}", str(v))
        return custom

    def get_locale_text(self, guild_id: Any, module: str, key: str, **kwargs) -> str:
        gid = str(guild_id)
        custom_key = f"{module}.{key}"

        if self.is_premium(gid):
            custom = self._custom_messages.get(gid, {}).get("locale", {}).get(custom_key)
            if custom and isinstance(custom, str):
                for k, v in kwargs.items():
                    custom = custom.replace(f"{{{k}}}", str(v))
                return custom

        try:
            from Niludetsu.locale import DEFAULT_LOCALE
            default_text = DEFAULT_LOCALE.get(module, {}).get(key, "")
        except ImportError:
            default_text = ""

        if default_text:
            for k, v in kwargs.items():
                default_text = default_text.replace(f"{{{k}}}", str(v))
        return default_text

    async def set_custom_value(self, guild_id: Any, module: str, key: str, value: Any):
        gid = str(guild_id)
        await database._neon.execute(
            """INSERT INTO public.custom_messages (guild_id, module, key, value, updated_at) 
               VALUES ($1, $2, $3, $4, now())
               ON CONFLICT (guild_id, module, key) 
               DO UPDATE SET value = $4, updated_at = now()""",
            gid, module, key, value
        )
        self._custom_messages.setdefault(gid, {}).setdefault(module, {})[key] = value

    async def delete_custom_value(self, guild_id: Any, module: str, key: str):
        gid = str(guild_id)
        await database._neon.execute(
            "DELETE FROM public.custom_messages WHERE guild_id = $1 AND module = $2 AND key = $3",
            gid, module, key
        )
        if gid in self._custom_messages and module in self._custom_messages[gid]:
            self._custom_messages[gid][module].pop(key, None)
