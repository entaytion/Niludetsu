import discord
from ..tools.Emojis import Emojis

from Niludetsu.webhooks.base import BaseLogger

class WebhookLogger(BaseLogger):
    """Логгер для действий с вебхуками."""

    async def log_webhook_create(self, log_channel: discord.TextChannel, channel: discord.TextChannel, webhook: discord.Webhook):
        description = f"**ID:** `{webhook.id}`\n**Название:** `{webhook.name}`\n**Канал:** {channel.mention}"
        creator = await self._safe_audit_log(channel.guild, discord.AuditLogAction.webhook_create, webhook.id, limit=5)
        if creator:
            description += f"\n**Создал:** {creator.mention} (`{creator.id}`)"
        await self.webhooks.send_log(
            log_channel, title=f"{Emojis.SUCCESS} Вебхук: добавлен",
            description=description,
            thumbnail_url=webhook.avatar.url if webhook.avatar else None,
            guild=channel.guild,
        )

    async def log_webhook_delete(self, log_channel: discord.TextChannel, channel: discord.TextChannel, webhook: discord.Webhook):
        description = f"**ID:** `{webhook.id}`\n**Название:** `{webhook.name}`\n**Канал:** {channel.mention}"
        deleter = await self._safe_audit_log(channel.guild, discord.AuditLogAction.webhook_delete, webhook.id, limit=5)
        if deleter:
            description += f"\n**Удалил:** {deleter.mention} (`{deleter.id}`)"
        await self.webhooks.send_log(
            log_channel, title=f"{Emojis.ERROR} Вебхук: удален",
            description=description,
            thumbnail_url=webhook.avatar.url if webhook.avatar else None,
            guild=channel.guild,
        )

    async def log_webhook_update(self, log_channel: discord.TextChannel, channel: discord.TextChannel, before: discord.Webhook, after: discord.Webhook):
        changes = []
        if before.name != after.name:
            changes.append(f"- Название: `{before.name}` ➜ `{after.name}`")
        before_avatar_url = before.avatar.url if before.avatar else None
        after_avatar_url = after.avatar.url if after.avatar else None
        if before_avatar_url != after_avatar_url:
            changes.append("- Аватар: изменён")
        # Sapphire: Webhook Channel Update
        before_ch = getattr(before, 'channel_id', None)
        after_ch = getattr(after, 'channel_id', None)
        if before_ch and after_ch and before_ch != after_ch:
            changes.append(f"- Канал: <#{before_ch}> ➜ <#{after_ch}>")
        if not changes:
            return
        description = f"**ID:** `{after.id}`\n**Название:** `{after.name}`\n**Канал:** {channel.mention}"
        updater = await self._safe_audit_log(channel.guild, discord.AuditLogAction.webhook_update, after.id, limit=5)
        if updater:
            description += f"\n**Изменил:** {updater.mention} (`{updater.id}`)"
        await self.webhooks.send_log(
            log_channel, title=f"{Emojis.UNKNOWN} Вебхук: обновлен",
            description=description,
            fields=[{"name": "Изменения:", "value": "\n".join(changes), "inline": False}],
            thumbnail_url=after.avatar.url if after.avatar else None,
            guild=channel.guild,
        )
