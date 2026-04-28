from __future__ import annotations

from typing import Any, Optional

from .base import BaseMixin


class ShopMixin(BaseMixin):
    async def list_shop_roles(self, guild_id: str) -> list[dict[str, Any]]:
        return await self.get_rows("roles", guild_id=str(guild_id))

    async def get_role_holders(self, guild_id: str, role_id: str) -> list[dict[str, Any]]:
        return await self.get_rows(
            "user_inventory", guild_id=str(guild_id), item_type="role", item_key=str(role_id)
        )

    async def delete_shop_roles(self, role_ids: list[int]) -> None:
        if not role_ids:
            return
        await self._neon.execute("DELETE FROM public.roles WHERE id = ANY($1)", role_ids)

    async def purge_inventory_roles(self, guild_id: str, role_discord_ids: list[str]) -> None:
        if not role_discord_ids:
            return
        await self._neon.execute(
            "DELETE FROM public.user_inventory WHERE guild_id = $1 AND item_type = 'role' AND item_key = ANY($2)",
            str(guild_id),
            role_discord_ids,
        )

    async def add_shop_role(self, data: dict[str, Any]) -> Optional[dict[str, Any]]:
        return await self.insert("roles", data)

    async def get_inventory_role(
        self, guild_id: str, user_id: str, role_id: str
    ) -> Optional[dict[str, Any]]:
        return await self.get_row(
            "user_inventory",
            guild_id=str(guild_id),
            user_id=str(user_id),
            item_type="role",
            item_key=str(role_id),
        )
