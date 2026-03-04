import discord
from Niludetsu import Emojis
from Niludetsu.development.Webhooks import Webhooks

class WebhookLogger:
    """
    Логгер для действий с вебхуками через вебхук (максимум информации).
    """
    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.webhooks = Webhooks(bot)

    async def log_webhook_create(self, log_channel: discord.TextChannel, channel: discord.TextChannel, webhook: discord.Webhook):
        title = f"{Emojis.SUCCESS} Вебхук: добавлен"
        description = f"**ID:** `{webhook.id}`\n**Название:** `{webhook.name}`\n**Канал:** {channel.mention}"
        guild = channel.guild
        user = None
        if guild:
            async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.webhook_create):
                if entry.target and entry.target.id == webhook.id:
                    description += f"\n**Создал:** {entry.user.mention} (`{entry.user.id}`)"
                    user = entry.user
                    break
        await self.webhooks.send_log(
            log_channel,
            title=title,
            description=description,
            thumbnail_url=webhook.avatar.url if webhook.avatar else None,
            guild=guild
        )

    async def log_webhook_delete(self, log_channel: discord.TextChannel, channel: discord.TextChannel, webhook: discord.Webhook):
        title = f"{Emojis.ERROR} Вебхук: удален"
        description = f"**ID:** `{webhook.id}`\n**Название:** `{webhook.name}`\n**Канал:** {channel.mention}"
        guild = channel.guild
        user = None
        if guild:
            async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.webhook_delete):
                if entry.target and entry.target.id == webhook.id:
                    description += f"\n**Удалил:** {entry.user.mention} (`{entry.user.id}`)"
                    user = entry.user
                    break
        await self.webhooks.send_log(
            log_channel,
            title=title,
            description=description,
            thumbnail_url=webhook.avatar.url if webhook.avatar else None,
            guild=guild
        )

    async def log_webhook_update(self, log_channel: discord.TextChannel, channel: discord.TextChannel, before: discord.Webhook, after: discord.Webhook):
        changes = []
        if before.name != after.name:
            changes.append(f"- Название: `{before.name}` ➜ `{after.name}`")
        # Аватар: проверяем на None или URL
        before_avatar_url = before.avatar.url if before.avatar else None
        after_avatar_url = after.avatar.url if after.avatar else None
        if before_avatar_url != after_avatar_url:
            changes.append("- Аватар: изменён")

        if not changes:
            return  # Нет реальных изменений

        title = f"{Emojis.UNKNOWN} Вебхук: обновлен"
        description = f"**ID:** `{after.id}`\n**Название:** `{after.name}`\n**Канал:** {channel.mention}"
        fields = [{"name": "Изменения:", "value": "\n".join(changes), "inline": False}]
        guild = channel.guild
        user = None
        if guild:
            async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.webhook_update):
                if entry.target and entry.target.id == after.id:
                    description += f"\n**Изменил:** {entry.user.mention} (`{entry.user.id}`)"
                    user = entry.user
                    break
        await self.webhooks.send_log(
            log_channel,
            title=title,
            description=description,
            fields=fields,
            thumbnail_url=after.avatar.url if after.avatar else None,
            guild=guild
        )

