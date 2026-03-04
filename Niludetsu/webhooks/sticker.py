import discord
from Niludetsu import Emojis
from Niludetsu.development.Webhooks import Webhooks

class StickerLogger:
    """
    Логгер для действий со стикерами через вебхук (максимум информации).
    """
    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.webhooks = Webhooks(bot)

    async def log_sticker_create(self, channel: discord.TextChannel, sticker: discord.Sticker):
        title = f"{Emojis.SUCCESS} Стикер: добавлен"
        description = f"**ID:** `{sticker.id}`\n**Название:** `{sticker.name}`"
        author = None
        async for entry in sticker.guild.audit_logs(limit=3, action=discord.AuditLogAction.sticker_create):
            if entry.target.id == sticker.id:
                description += f"\n**Создал:** {entry.user.mention} (`{entry.user.id}`)"
                author = entry.user
                break
        await self.webhooks.send_log(
            channel,
            title=title,
            description=description,
            thumbnail_url=sticker.url if hasattr(sticker, 'url') else None,
            guild=sticker.guild
        )

    async def log_sticker_delete(self, channel: discord.TextChannel, sticker: discord.Sticker):
        title = f"{Emojis.ERROR} Стикер: удален"
        description = f"**ID:** `{sticker.id}`\n**Название:** `{sticker.name}`"
        author = None
        async for entry in sticker.guild.audit_logs(limit=3, action=discord.AuditLogAction.sticker_delete):
            if entry.target.id == sticker.id:
                description += f"\n**Удалил:** {entry.user.mention} (`{entry.user.id}`)"
                author = entry.user
                break
        await self.webhooks.send_log(
            channel,
            title=title,
            description=description,
            thumbnail_url=sticker.url if hasattr(sticker, 'url') else None,
            guild=sticker.guild
        )

    async def log_sticker_update(self, channel: discord.TextChannel, before: discord.Sticker, after: discord.Sticker):
        title = f"{Emojis.UNKNOWN} Стикер: обновлен"
        fields = []
        if before.name != after.name:
            fields.append({
                "name": "> Изменения:",
                "value": f"- Название: `{before.name}` ➜ `{after.name}`",
                "inline": False
            })
        if before.description != after.description:
            fields.append({
                "name": "> Изменения:",
                "value": f"- Описание: `{before.description or '—'}` ➜ `{after.description or '—'}`",
                "inline": False
            })
        if not fields:
            return
        description = f"**ID:** `{after.id}`\n**Название:** `{after.name}`"
        author = None
        async for entry in after.guild.audit_logs(limit=3, action=discord.AuditLogAction.sticker_update):
            if entry.target.id == after.id:
                description += f"\n**Изменил:** {entry.user.mention} (`{entry.user.id}`)"
                author = entry.user
                break
        await self.webhooks.send_log(
            channel,
            title=title,
            description=description,
            fields=fields,
            thumbnail_url=after.url if hasattr(after, 'url') else None,
            guild=after.guild
        ) 

