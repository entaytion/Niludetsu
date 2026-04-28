import discord
from ..tools.Emojis import Emojis

from Niludetsu.webhooks.base import BaseLogger

class StickerLogger(BaseLogger):
    """Логгер для действий со стикерами."""

    async def log_sticker_create(self, channel: discord.TextChannel, sticker: discord.Sticker):
        description = f"**ID:** `{sticker.id}`\n**Название:** `{sticker.name}`"
        creator = await self._safe_audit_log(sticker.guild, discord.AuditLogAction.sticker_create, sticker.id)
        if creator:
            description += f"\n**Создал:** {creator.mention} (`{creator.id}`)"
        await self.webhooks.send_log(
            channel, title=f"{Emojis.SUCCESS} Стикер: добавлен",
            description=description,
            thumbnail_url=sticker.url if hasattr(sticker, 'url') else None,
            guild=sticker.guild,
        )

    async def log_sticker_delete(self, channel: discord.TextChannel, sticker: discord.Sticker):
        description = f"**ID:** `{sticker.id}`\n**Название:** `{sticker.name}`"
        deleter = await self._safe_audit_log(sticker.guild, discord.AuditLogAction.sticker_delete, sticker.id)
        if deleter:
            description += f"\n**Удалил:** {deleter.mention} (`{deleter.id}`)"
        await self.webhooks.send_log(
            channel, title=f"{Emojis.ERROR} Стикер: удален",
            description=description,
            thumbnail_url=sticker.url if hasattr(sticker, 'url') else None,
            guild=sticker.guild,
        )

    async def log_sticker_update(self, channel: discord.TextChannel, before: discord.Sticker, after: discord.Sticker):
        fields = []
        if before.name != after.name:
            fields.append({"name": "> Изменения:", "value": f"- Название: `{before.name}` ➜ `{after.name}`", "inline": False})
        if before.description != after.description:
            fields.append({"name": "> Изменения:", "value": f"- Описание: `{before.description or '—'}` ➜ `{after.description or '—'}`", "inline": False})
        # Sapphire: Sticker Related Emoji Update
        if getattr(before, 'emoji', None) != getattr(after, 'emoji', None):
            fields.append({"name": "> Изменения:", "value": f"- Эмодзи: `{getattr(before, 'emoji', '—')}` ➜ `{getattr(after, 'emoji', '—')}`", "inline": False})
        if not fields:
            return
        description = f"**ID:** `{after.id}`\n**Название:** `{after.name}`"
        updater = await self._safe_audit_log(after.guild, discord.AuditLogAction.sticker_update, after.id)
        if updater:
            description += f"\n**Изменил:** {updater.mention} (`{updater.id}`)"
        await self.webhooks.send_log(
            channel, title=f"{Emojis.UNKNOWN} Стикер: обновлен",
            description=description, fields=fields,
            thumbnail_url=after.url if hasattr(after, 'url') else None, guild=after.guild,
        )
