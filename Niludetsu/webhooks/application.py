import discord
from ..tools.Emojis import Emojis
from Niludetsu.locale import _

from Niludetsu.webhooks.base import BaseLogger


class ApplicationLogger(BaseLogger):
    """Логгер для событий приложений (интеграции)."""

    async def log_app_add(self, channel: discord.TextChannel, app: discord.Integration):
        t = _(guild_id=channel.guild.id, bot=self.bot)
        description = f"**ID:** `{app.id}`\n**{t('audit_log', 'field_app_name')}:** `{app.name}`\n**{t('audit_log', 'field_app_type')}:** `{app.type}`"
        if hasattr(app, "user") and app.user:
            description += f"\n**{t('audit_log', 'field_app_added')}:** {app.user.mention} ({app.user.id})"
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.SUCCESS} {t('audit_log', 'app_add_title')}",
            description=description, fields=[],
            thumbnail_url=getattr(app, 'icon_url', None), guild=channel.guild,
        )

    async def log_app_remove(self, channel: discord.TextChannel, app: discord.Integration, remover: discord.User = None):
        t = _(guild_id=channel.guild.id, bot=self.bot)
        description = f"**ID:** `{app.id}`\n**{t('audit_log', 'field_app_name')}:** `{app.name}`\n**{t('audit_log', 'field_app_type')}:** `{app.type}`"
        if remover:
            description += f"\n**{t('audit_log', 'field_app_removed')}:** {remover.mention} ({remover.id})"
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.ERROR} {t('audit_log', 'app_remove_title')}",
            description=description, fields=[],
            thumbnail_url=getattr(app, 'icon_url', None), guild=channel.guild,
        )

    async def log_app_update(self, channel: discord.TextChannel, before: discord.Integration, after: discord.Integration, updater: discord.User = None):
        t = _(guild_id=channel.guild.id, bot=self.bot)
        description = f"**ID:** `{after.id}`\n**{t('audit_log', 'field_app_name')}:** `{after.name}`\n**{t('audit_log', 'field_app_type')}:** `{after.type}`"
        if updater:
            description += f"\n**{t('audit_log', 'field_app_updated')}:** {updater.mention} ({updater.id})"
        fields = []
        if hasattr(before, 'enabled') and hasattr(after, 'enabled') and before.enabled != after.enabled:
            fields.append({"name": t('audit_log', 'field_app_status'), "value": t('audit_log', 'automod_enabled') if after.enabled else t('audit_log', 'automod_disabled'), "inline": True})
        if hasattr(before, 'expire_behavior') and hasattr(after, 'expire_behavior') and before.expire_behavior != after.expire_behavior:
            fields.append({"name": t('audit_log', 'field_app_expire_behavior'), "value": f"{before.expire_behavior} ➜ {after.expire_behavior}", "inline": True})
        if hasattr(before, 'expire_grace_period') and hasattr(after, 'expire_grace_period') and before.expire_grace_period != after.expire_grace_period:
            fields.append({"name": t('audit_log', 'field_app_expire_grace'), "value": f"{before.expire_grace_period} ➜ {after.expire_grace_period}", "inline": True})
        if hasattr(before, 'syncing') and hasattr(after, 'syncing') and before.syncing != after.syncing:
            fields.append({"name": t('audit_log', 'field_app_syncing'), "value": t('audit_log', 'yes') if after.syncing else t('audit_log', 'no'), "inline": True})
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.UNKNOWN} {t('audit_log', 'app_update_title')}",
            description=description, fields=fields,
            thumbnail_url=getattr(after, 'icon_url', None), guild=channel.guild,
        )

    async def log_app_permission_update(self, channel: discord.TextChannel, app_command, updater: discord.User = None):
        t = _(guild_id=channel.guild.id, bot=self.bot)
        description = f"**ID:** `{app_command.id}`\n**{t('audit_log', 'field_app_command')}:** `{app_command.name}`\n**{t('audit_log', 'field_app_type')}:** `{app_command.type}`"
        if updater:
            description += f"\n**{t('audit_log', 'field_app_updated')}:** {updater.mention} ({updater.id})"
        fields = []
        if hasattr(app_command, 'permissions') and app_command.permissions:
            for permission in app_command.permissions:
                target = permission.target
                target_name = getattr(target, 'name', str(target.id))
                permission_type = t('audit_log', 'app_perm_allowed') if permission.permission else t('audit_log', 'app_perm_denied')
                fields.append({"name": f"{target_name}", "value": f"{permission_type}", "inline": True})
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.UNKNOWN} {t('audit_log', 'app_perms_title')}",
            description=description, fields=fields,
            thumbnail_url=getattr(app_command, 'application', None) and getattr(app_command.application, 'icon_url', None),
            guild=channel.guild,
        )
