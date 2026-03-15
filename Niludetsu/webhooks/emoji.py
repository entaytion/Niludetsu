import discord
from Niludetsu import Emojis
from Niludetsu.webhooks.base import BaseLogger


class EmojiLogger(BaseLogger):
    """Логгер для действий с эмодзи."""

    async def log_emoji_create(self, channel: discord.TextChannel, emoji: discord.Emoji):
        description = f"**ID:** `{emoji.id}`\n**Название:** `:{emoji.name}:`"
        creator = await self._safe_audit_log(emoji.guild, discord.AuditLogAction.emoji_create, emoji.id)
        if creator:
            description += f"\n**Создал:** {creator.mention} (`{creator.id}`)"
        await self.webhooks.send_log(
            channel, title=f"{Emojis.SUCCESS} Эмодзи: добавлено",
            description=description, thumbnail_url=emoji.url, guild=emoji.guild,
        )

    async def log_emoji_delete(self, channel: discord.TextChannel, emoji: discord.Emoji):
        description = f"**ID:** `{emoji.id}`\n**Название:** `:{emoji.name}:`"
        deleter = await self._safe_audit_log(emoji.guild, discord.AuditLogAction.emoji_delete, emoji.id)
        if deleter:
            description += f"\n**Удалил:** {deleter.mention} (`{deleter.id}`)"
        await self.webhooks.send_log(
            channel, title=f"{Emojis.ERROR} Эмодзи: удалено",
            description=description, thumbnail_url=emoji.url, guild=emoji.guild,
        )

    async def log_emoji_update(self, channel: discord.TextChannel, before: discord.Emoji, after: discord.Emoji):
        fields = []
        if before.name != after.name:
            fields.append({"name": "> Изменения:", "value": f"- Название: `:{before.name}:` ➜ `:{after.name}:`", "inline": False})
        # Sapphire: Emoji Roles Update
        before_roles = set(before.roles) if before.roles else set()
        after_roles = set(after.roles) if after.roles else set()
        if before_roles != after_roles:
            added = after_roles - before_roles
            removed = before_roles - after_roles
            if added:
                fields.append({"name": "> Роли (добавлены):", "value": ", ".join(r.mention for r in added), "inline": False})
            if removed:
                fields.append({"name": "> Роли (убраны):", "value": ", ".join(r.mention for r in removed), "inline": False})
        if not fields:
            return
        description = f"**ID:** `{after.id}`\n**Название:** `:{after.name}:`"
        updater = await self._safe_audit_log(after.guild, discord.AuditLogAction.emoji_update, after.id)
        if updater:
            description += f"\n**Изменил:** {updater.mention} (`{updater.id}`)"
        await self.webhooks.send_log(
            channel, title=f"{Emojis.UNKNOWN} Эмодзи: обновлено",
            description=description, fields=fields, thumbnail_url=after.url, guild=after.guild,
        )
