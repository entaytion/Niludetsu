import discord
from ..tools.Emojis import Emojis
from Niludetsu.locale import _

from Niludetsu.webhooks.base import BaseLogger

class AutoModLogger(BaseLogger):

    async def log_automod_rule_create(self, channel: discord.TextChannel, rule: discord.AutoModRule):
        t = _(guild_id=channel.guild.id, bot=self.bot)
        description = f"**{t('audit_log', 'field_id')}:** `{rule.id}`\n**{t('audit_log', 'field_automod_name')}:** `{rule.name}`\n**{t('audit_log', 'field_automod_type')}:** `{rule.trigger_type}`"
        fields = []
        if rule.creator:
            fields.append({"name": t('audit_log', 'created_by'), "value": f"{rule.creator.mention} ({rule.creator.id})", "inline": True})
        if rule.trigger_metadata:
            fields.append({"name": t('audit_log', 'field_automod_conditions'), "value": f"{rule.trigger_metadata}", "inline": False})
        if rule.actions:
            actions = ", ".join([str(a.type) for a in rule.actions])
            fields.append({"name": t('audit_log', 'field_automod_actions'), "value": actions, "inline": False})
        if getattr(rule, 'exempt_roles', None):
            fields.append({"name": t('audit_log', 'field_automod_excluded_roles'), "value": ", ".join(r.mention for r in rule.exempt_roles), "inline": False})
        if getattr(rule, 'exempt_channels', None):
            fields.append({"name": t('audit_log', 'field_automod_excluded_channels'), "value": ", ".join(f"<#{c.id}>" for c in rule.exempt_channels), "inline": False})
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.SUCCESS} {t('audit_log', 'automod_rule_create')}",
            description=description, fields=fields, guild=channel.guild,
        )

    async def log_automod_rule_update(self, channel: discord.TextChannel, rule: discord.AutoModRule):
        t = _(guild_id=channel.guild.id, bot=self.bot)
        description = f"**{t('audit_log', 'field_id')}:** `{rule.id}`\n**{t('audit_log', 'field_automod_name')}:** `{rule.name}`\n**{t('audit_log', 'field_automod_type')}:** `{rule.trigger_type}`"
        fields = []
        if hasattr(rule, 'enabled'):
            fields.append({"name": t('audit_log', 'field_automod_status'), "value": f"{t('audit_log', 'automod_enabled') if rule.enabled else t('audit_log', 'automod_disabled')}", "inline": True})
        if rule.creator:
            fields.append({"name": t('audit_log', 'updated_by'), "value": f"{rule.creator.mention} ({rule.creator.id})", "inline": True})
        if rule.trigger_metadata:
            fields.append({"name": t('audit_log', 'field_automod_conditions'), "value": f"{rule.trigger_metadata}", "inline": False})
        if rule.actions:
            actions = ", ".join([str(a.type) for a in rule.actions])
            fields.append({"name": t('audit_log', 'field_automod_actions'), "value": actions, "inline": False})
        if getattr(rule, 'exempt_roles', None):
            fields.append({"name": t('audit_log', 'field_automod_excluded_roles'), "value": ", ".join(r.mention for r in rule.exempt_roles), "inline": False})
        if getattr(rule, 'exempt_channels', None):
            fields.append({"name": t('audit_log', 'field_automod_excluded_channels'), "value": ", ".join(f"<#{c.id}>" for c in rule.exempt_channels), "inline": False})
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.UNKNOWN} {t('audit_log', 'automod_rule_update')}",
            description=description, fields=fields, guild=channel.guild,
        )

    async def log_automod_rule_delete(self, channel: discord.TextChannel, rule: discord.AutoModRule):
        t = _(guild_id=channel.guild.id, bot=self.bot)
        description = f"**{t('audit_log', 'field_id')}:** `{rule.id}`\n**{t('audit_log', 'field_automod_name')}:** `{rule.name}`\n**{t('audit_log', 'field_automod_type')}:** `{rule.trigger_type}`"
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.ERROR} {t('audit_log', 'automod_rule_delete')}",
            description=description, fields=[], guild=channel.guild,
        )

    async def log_automod_action(self, channel: discord.TextChannel, execution: discord.AutoModAction):
        t = _(guild_id=channel.guild.id, bot=self.bot)
        description = f"**{t('audit_log', 'field_automod_rule_id')}:** `{execution.rule_id}`\n**{t('audit_log', 'field_automod_action_type')}:** `{execution.action.type}`"
        fields = []
        if hasattr(execution, 'user_id'):
            fields.append({"name": t('audit_log', 'field_user'), "value": f"<@{execution.user_id}> ({execution.user_id})", "inline": True})
        if hasattr(execution, 'channel_id'):
            fields.append({"name": t('audit_log', 'field_channel'), "value": f"<#{execution.channel_id}> ({execution.channel_id})", "inline": True})
        if hasattr(execution, 'content') and execution.content:
            fields.append({"name": t('audit_log', 'field_automod_content'), "value": f"```{execution.content[:1024]}```", "inline": False})
        if hasattr(execution, 'matched_keyword') and execution.matched_keyword:
            fields.append({"name": t('audit_log', 'field_automod_keyword'), "value": f"{execution.matched_keyword}", "inline": True})
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.ERROR} {t('audit_log', 'automod_action_title')}",
            description=description, fields=fields, guild=channel.guild,
        )
