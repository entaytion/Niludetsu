import discord
from ..tools.Emojis import Emojis

from Niludetsu.webhooks.base import BaseLogger

class ApplicationLogger(BaseLogger):
    """Логгер для событий приложений (интеграции)."""

    async def log_app_add(self, channel: discord.TextChannel, app: discord.Integration):
        description = f"**ID:** `{app.id}`\n**Название:** `{app.name}`\n**Тип:** `{app.type}`"
        if hasattr(app, "user") and app.user:
            description += f"\n**Добавил:** {app.user.mention} ({app.user.id})"
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.SUCCESS} Приложение: добавлено",
            description=description, fields=[],
            thumbnail_url=getattr(app, 'icon_url', None), guild=channel.guild,
        )

    async def log_app_remove(self, channel: discord.TextChannel, app: discord.Integration, remover: discord.User = None):
        description = f"**ID:** `{app.id}`\n**Название:** `{app.name}`\n**Тип:** `{app.type}`"
        if remover:
            description += f"\n**Удалил:** {remover.mention} ({remover.id})"
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.ERROR} Приложение: удалено",
            description=description, fields=[],
            thumbnail_url=getattr(app, 'icon_url', None), guild=channel.guild,
        )

    async def log_app_update(self, channel: discord.TextChannel, before: discord.Integration, after: discord.Integration, updater: discord.User = None):
        description = f"**ID:** `{after.id}`\n**Название:** `{after.name}`\n**Тип:** `{after.type}`"
        if updater:
            description += f"\n**Обновил:** {updater.mention} ({updater.id})"
        fields = []
        if hasattr(before, 'enabled') and hasattr(after, 'enabled') and before.enabled != after.enabled:
            fields.append({"name": "Статус", "value": f"{'Включено' if after.enabled else 'Выключено'}", "inline": True})
        if hasattr(before, 'expire_behavior') and hasattr(after, 'expire_behavior') and before.expire_behavior != after.expire_behavior:
            fields.append({"name": "Поведение при истечении", "value": f"{before.expire_behavior} ➜ {after.expire_behavior}", "inline": True})
        if hasattr(before, 'expire_grace_period') and hasattr(after, 'expire_grace_period') and before.expire_grace_period != after.expire_grace_period:
            fields.append({"name": "Период отсрочки", "value": f"{before.expire_grace_period} ➜ {after.expire_grace_period}", "inline": True})
        if hasattr(before, 'syncing') and hasattr(after, 'syncing') and before.syncing != after.syncing:
            fields.append({"name": "Синхронизация", "value": f"{'Да' if after.syncing else 'Нет'}", "inline": True})
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.UNKNOWN} Приложение: изменено",
            description=description, fields=fields,
            thumbnail_url=getattr(after, 'icon_url', None), guild=channel.guild,
        )

    async def log_app_permission_update(self, channel: discord.TextChannel, app_command, updater: discord.User = None):
        description = f"**ID:** `{app_command.id}`\n**Команда:** `{app_command.name}`\n**Тип:** `{app_command.type}`"
        if updater:
            description += f"\n**Обновил:** {updater.mention} ({updater.id})"
        fields = []
        if hasattr(app_command, 'permissions') and app_command.permissions:
            for permission in app_command.permissions:
                target = permission.target
                target_name = getattr(target, 'name', str(target.id))
                permission_type = "разрешено" if permission.permission else "запрещено"
                fields.append({"name": f"{target_name}", "value": f"{permission_type}", "inline": True})
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.UNKNOWN} Приложение: обновление разрешений",
            description=description, fields=fields,
            thumbnail_url=getattr(app_command, 'application', None) and getattr(app_command.application, 'icon_url', None),
            guild=channel.guild,
        )
