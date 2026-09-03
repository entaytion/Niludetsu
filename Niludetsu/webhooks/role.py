import discord
from ..tools.Emojis import Emojis

from Niludetsu.locale import _
from Niludetsu.webhooks.base import BaseLogger
from Niludetsu.webhooks.constants import permissions_list, permissions_diff

class RoleLogger(BaseLogger):

    async def log_role_create(self, channel: discord.TextChannel, role: discord.Role):
        t = _(guild_id=role.guild.id, bot=self.bot)
        description = (
            f"**{t('audit_log', 'field_name')}:** {role.mention}\n**{t('audit_log', 'field_id')}:** `{role.id}`\n**{t('audit_log', 'field_color')}:** `{str(role.color)}`\n"
            f"**{t('audit_log', 'field_position')}:** `{role.position}`\n"
            f"**{t('audit_log', 'field_hoist')}:** `{t('audit_log', 'yes') if role.hoist else t('audit_log', 'no')}`\n"
            f"**{t('audit_log', 'field_mentionable')}:** `{t('audit_log', 'yes') if role.mentionable else t('audit_log', 'no')}`"
        )
        if role.icon:
            description += f"\n**{t('audit_log', 'field_icon')}:** `{t('audit_log', 'field_has_icon')}`"
        perms = permissions_list(role.permissions)
        fields = []
        if perms:
            fields.append({"name": t('audit_log', 'field_perms'), "value": ", ".join(f'`{p}`' for p in perms), "inline": False})
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.SUCCESS} {t('audit_log', 'role_create_title')}",
            description=description, fields=fields if fields else None,
            thumbnail_url=role.icon.url if role.icon else None, guild=role.guild,
        )

    async def log_role_delete(self, channel: discord.TextChannel, role: discord.Role):
        t = _(guild_id=role.guild.id, bot=self.bot)
        description = f"**{t('audit_log', 'field_name')}:** `{role.name}`\n**{t('audit_log', 'field_id')}:** `{role.id}`\n**{t('audit_log', 'field_color')}:** `{str(role.color)}`"
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.ERROR} {t('audit_log', 'role_delete_title')}",
            description=description,
            thumbnail_url=role.icon.url if role.icon else None, guild=role.guild,
        )

    async def log_role_update(self, channel: discord.TextChannel, before: discord.Role, after: discord.Role):
        t = _(guild_id=after.guild.id, bot=self.bot)
        description = f"**{t('audit_log', 'field_role')}:** {after.mention}\n**{t('audit_log', 'field_id')}:** `{after.id}`"
        fields = []
        if before.name != after.name:
            fields.append({"name": t('audit_log', 'field_change_name'), "value": f"`{before.name}` ➜ `{after.name}`", "inline": False})
        if before.color != after.color:
            fields.append({"name": t('audit_log', 'field_color'), "value": f"`{str(before.color)}` ➜ `{str(after.color)}`", "inline": False})
        if before.hoist != after.hoist:
            fields.append({"name": t('audit_log', 'field_hoist'), "value": f"`{t('audit_log', 'yes') if before.hoist else t('audit_log', 'no')}` ➜ `{t('audit_log', 'yes') if after.hoist else t('audit_log', 'no')}`", "inline": False})
        if before.mentionable != after.mentionable:
            fields.append({"name": t('audit_log', 'field_mentionable'), "value": f"`{t('audit_log', 'yes') if before.mentionable else t('audit_log', 'no')}` ➜ `{t('audit_log', 'yes') if after.mentionable else t('audit_log', 'no')}`", "inline": False})
        if before.icon != after.icon:
            fields.append({"name": t('audit_log', 'field_icon'), "value": f"`{t('audit_log', 'field_has_icon') if before.icon else t('audit_log', 'no')}` ➜ `{t('audit_log', 'field_has_icon') if after.icon else t('audit_log', 'no')}`", "inline": False})
        if before.permissions != after.permissions:
            added, removed = permissions_diff(before.permissions, after.permissions)
            if added:
                fields.append({"name": t('audit_log', 'field_perms_added'), "value": ", ".join(f'`{p}`' for p in added), "inline": False})
            if removed:
                fields.append({"name": t('audit_log', 'field_perms_removed'), "value": ", ".join(f'`{p}`' for p in removed), "inline": False})
        if not fields:
            return
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.UNKNOWN} {t('audit_log', 'role_update_title')}",
            description=description, fields=fields,
            thumbnail_url=after.icon.url if after.icon else None, guild=after.guild,
        )
