from ..locale import _
from ..tools.Emojis import Emojis

from Niludetsu.webhooks.base import BaseLogger

class WebhookLogger(BaseLogger):
    """Логгер для действий с вебхуками."""

    async def log_webhook_create(self, log_channel: discord.TextChannel, channel: discord.TextChannel, webhook: discord.Webhook):
        t = _(guild_id=channel.guild.id, bot=self.bot)
        description = f"**ID:** `{webhook.id}`\n**{t('audit_log', 'field_name')}:** `{webhook.name}`\n**{t('audit_log', 'field_channel')}:** {channel.mention}"
        creator = await self._safe_audit_log(channel.guild, discord.AuditLogAction.webhook_create, webhook.id, limit=5)
        if creator:
            description += f"\n**{t('audit_log', 'created_by')}:** {creator.mention} (`{creator.id}`)"
        await self.webhooks.send_log(
            log_channel, title=f"{Emojis.SUCCESS} {t('audit_log', 'webhook_created')}",
            description=description,
            thumbnail_url=webhook.avatar.url if webhook.avatar else None,
            guild=channel.guild,
        )

    async def log_webhook_delete(self, log_channel: discord.TextChannel, channel: discord.TextChannel, webhook: discord.Webhook):
        t = _(guild_id=channel.guild.id, bot=self.bot)
        description = f"**ID:** `{webhook.id}`\n**{t('audit_log', 'field_name')}:** `{webhook.name}`\n**{t('audit_log', 'field_channel')}:** {channel.mention}"
        deleter = await self._safe_audit_log(channel.guild, discord.AuditLogAction.webhook_delete, webhook.id, limit=5)
        if deleter:
            description += f"\n**{t('audit_log', 'deleted_by')}:** {deleter.mention} (`{deleter.id}`)"
        await self.webhooks.send_log(
            log_channel, title=f"{Emojis.ERROR} {t('audit_log', 'webhook_deleted')}",
            description=description,
            thumbnail_url=webhook.avatar.url if webhook.avatar else None,
            guild=channel.guild,
        )

    async def log_webhook_update(self, log_channel: discord.TextChannel, channel: discord.TextChannel, before: discord.Webhook, after: discord.Webhook):
        t = _(guild_id=channel.guild.id, bot=self.bot)
        changes = []
        if before.name != after.name:
            changes.append(f"- {t('audit_log', 'field_name')}: `{before.name}` ➜ `{after.name}`")
        before_avatar_url = before.avatar.url if before.avatar else None
        after_avatar_url = after.avatar.url if after.avatar else None
        if before_avatar_url != after_avatar_url:
            changes.append(f"- {t('audit_log', 'field_avatar')}: {t('audit_log', 'changed')}")
        # Sapphire: Webhook Channel Update
        before_ch = getattr(before, 'channel_id', None)
        after_ch = getattr(after, 'channel_id', None)
        if before_ch and after_ch and before_ch != after_ch:
            changes.append(f"- {t('audit_log', 'field_channel')}: <#{before_ch}> ➜ <#{after_ch}>")
        if not changes:
            return
        description = f"**ID:** `{after.id}`\n**{t('audit_log', 'field_name')}:** `{after.name}`\n**{t('audit_log', 'field_channel')}:** {channel.mention}"
        updater = await self._safe_audit_log(channel.guild, discord.AuditLogAction.webhook_update, after.id, limit=5)
        if updater:
            description += f"\n**{t('audit_log', 'updated_by')}:** {updater.mention} (`{updater.id}`)"
        await self.webhooks.send_log(
            log_channel, title=f"{Emojis.UNKNOWN} {t('audit_log', 'webhook_updated')}",
            description=description,
            fields=[{"name": t("audit_log", "changes"), "value": "\n".join(changes), "inline": False}],
            thumbnail_url=after.avatar.url if after.avatar else None,
            guild=channel.guild,
        )
