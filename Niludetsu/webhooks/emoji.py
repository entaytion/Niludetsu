import discord
from ..tools.Emojis import Emojis

from Niludetsu.locale import _
from Niludetsu.webhooks.base import BaseLogger

class EmojiLogger(BaseLogger):

    async def log_emoji_create(self, channel: discord.TextChannel, emoji: discord.Emoji):
        t = _(guild_id=emoji.guild.id, bot=self.bot)
        description = f"**{t('audit_log', 'field_id')}:** `{emoji.id}`\n**{t('audit_log', 'field_name')}:** `:{emoji.name}:`"
        creator = await self._safe_audit_log(emoji.guild, discord.AuditLogAction.emoji_create, emoji.id)
        if creator:
            description += f"\n**{t('audit_log', 'created_by')}** {creator.mention} (`{creator.id}`)"
        await self.webhooks.send_log(
            channel, title=f"{Emojis.SUCCESS} {t('audit_log', 'emoji_create_title')}",
            description=description, thumbnail_url=emoji.url, guild=emoji.guild,
        )

    async def log_emoji_delete(self, channel: discord.TextChannel, emoji: discord.Emoji):
        t = _(guild_id=emoji.guild.id, bot=self.bot)
        description = f"**{t('audit_log', 'field_id')}:** `{emoji.id}`\n**{t('audit_log', 'field_name')}:** `:{emoji.name}:`"
        deleter = await self._safe_audit_log(emoji.guild, discord.AuditLogAction.emoji_delete, emoji.id)
        if deleter:
            description += f"\n**{t('audit_log', 'deleted_by')}** {deleter.mention} (`{deleter.id}`)"
        await self.webhooks.send_log(
            channel, title=f"{Emojis.ERROR} {t('audit_log', 'emoji_delete_title')}",
            description=description, thumbnail_url=emoji.url, guild=emoji.guild,
        )

    async def log_emoji_update(self, channel: discord.TextChannel, before: discord.Emoji, after: discord.Emoji):
        t = _(guild_id=after.guild.id, bot=self.bot)
        fields = []
        if before.name != after.name:
            fields.append({"name": f"> {t('audit_log', 'changes')}", "value": f"- {t('audit_log', 'field_name')}: `:{before.name}:` ➜ `:{after.name}:`", "inline": False})
        before_roles = set(before.roles) if before.roles else set()
        after_roles = set(after.roles) if after.roles else set()
        if before_roles != after_roles:
            added = after_roles - before_roles
            removed = before_roles - after_roles
            if added:
                fields.append({"name": f"> {t('audit_log', 'added_roles')}:", "value": ", ".join(r.mention for r in added), "inline": False})
            if removed:
                fields.append({"name": f"> {t('audit_log', 'removed_roles')}:", "value": ", ".join(r.mention for r in removed), "inline": False})
        if not fields:
            return
        description = f"**{t('audit_log', 'field_id')}:** `{after.id}`\n**{t('audit_log', 'field_name')}:** `:{after.name}:`"
        updater = await self._safe_audit_log(after.guild, discord.AuditLogAction.emoji_update, after.id)
        if updater:
            description += f"\n**{t('audit_log', 'updated_by')}** {updater.mention} (`{updater.id}`)"
        await self.webhooks.send_log(
            channel, title=f"{Emojis.UNKNOWN} {t('audit_log', 'emoji_update_title')}",
            description=description, fields=fields, thumbnail_url=after.url, guild=after.guild,
        )
