import discord
from ..tools.Emojis import Emojis

from Niludetsu.webhooks.base import BaseLogger
from Niludetsu.webhooks.constants import permissions_list, permissions_diff

class RoleLogger(BaseLogger):
    """Логгер для событий ролей."""

    async def log_role_create(self, channel: discord.TextChannel, role: discord.Role):
        description = (
            f"**Название:** {role.mention}\n**ID:** `{role.id}`\n**Цвет:** `{str(role.color)}`\n"
            f"**Позиция:** `{role.position}`\n"
            f"**Отображается отдельно:** `{'Да' if role.hoist else 'Нет'}`\n"
            f"**Упоминаемая:** `{'Да' if role.mentionable else 'Нет'}`"
        )
        if role.icon:
            description += f"\n**Иконка:** `Есть`"
        perms = permissions_list(role.permissions)
        fields = []
        if perms:
            fields.append({"name": "Права", "value": ", ".join(f'`{p}`' for p in perms), "inline": False})
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.SUCCESS} Роль: создана",
            description=description, fields=fields if fields else None,
            thumbnail_url=role.icon.url if role.icon else None, guild=role.guild,
        )

    async def log_role_delete(self, channel: discord.TextChannel, role: discord.Role):
        description = f"**Название:** `{role.name}`\n**ID:** `{role.id}`\n**Цвет:** `{str(role.color)}`"
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.ERROR} Роль: удалена",
            description=description,
            thumbnail_url=role.icon.url if role.icon else None, guild=role.guild,
        )

    async def log_role_update(self, channel: discord.TextChannel, before: discord.Role, after: discord.Role):
        description = f"**Роль:** {after.mention}\n**ID:** `{after.id}`"
        fields = []
        if before.name != after.name:
            fields.append({"name": "Название", "value": f"`{before.name}` ➜ `{after.name}`", "inline": False})
        if before.color != after.color:
            fields.append({"name": "Цвет", "value": f"`{str(before.color)}` ➜ `{str(after.color)}`", "inline": False})
        if before.hoist != after.hoist:
            fields.append({"name": "Отображается отдельно", "value": f"`{'Да' if before.hoist else 'Нет'}` ➜ `{'Да' if after.hoist else 'Нет'}`", "inline": False})
        if before.mentionable != after.mentionable:
            fields.append({"name": "Упоминаемая", "value": f"`{'Да' if before.mentionable else 'Нет'}` ➜ `{'Да' if after.mentionable else 'Нет'}`", "inline": False})
        if before.icon != after.icon:
            fields.append({"name": "Иконка", "value": f"`{'Есть' if before.icon else 'Нет'}` ➜ `{'Есть' if after.icon else 'Нет'}`", "inline": False})
        if before.permissions != after.permissions:
            added, removed = permissions_diff(before.permissions, after.permissions)
            if added:
                fields.append({"name": "Добавлены права", "value": ", ".join(f'`{p}`' for p in added), "inline": False})
            if removed:
                fields.append({"name": "Удалены права", "value": ", ".join(f'`{p}`' for p in removed), "inline": False})
        if not fields:
            return
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.UNKNOWN} Роль: изменена",
            description=description, fields=fields,
            thumbnail_url=after.icon.url if after.icon else None, guild=after.guild,
        )
