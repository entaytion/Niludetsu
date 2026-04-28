import discord
from ..tools.Emojis import Emojis

from Niludetsu.webhooks.base import BaseLogger

class AutoModLogger(BaseLogger):
    """Логгер для AutoMod с детализацией по Sapphire."""

    async def log_automod_rule_create(self, channel: discord.TextChannel, rule: discord.AutoModRule):
        description = f"**ID:** `{rule.id}`\n**Имя:** `{rule.name}`\n**Тип:** `{rule.trigger_type}`"
        fields = []
        if rule.creator:
            fields.append({"name": "Создатель", "value": f"{rule.creator.mention} ({rule.creator.id})", "inline": True})
        if rule.trigger_metadata:
            fields.append({"name": "Условия", "value": f"{rule.trigger_metadata}", "inline": False})
        if rule.actions:
            actions = ", ".join([str(a.type) for a in rule.actions])
            fields.append({"name": "Действия", "value": actions, "inline": False})
        if getattr(rule, 'exempt_roles', None):
            fields.append({"name": "Исключённые роли", "value": ", ".join(r.mention for r in rule.exempt_roles), "inline": False})
        if getattr(rule, 'exempt_channels', None):
            fields.append({"name": "Исключённые каналы", "value": ", ".join(f"<#{c.id}>" for c in rule.exempt_channels), "inline": False})
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.SUCCESS} AutoMod: правило создано",
            description=description, fields=fields, guild=channel.guild,
        )

    async def log_automod_rule_update(self, channel: discord.TextChannel, rule: discord.AutoModRule):
        """Sapphire разделяет на toggle/name/actions/content/roles/channels/whitelist — мы логируем текущее состояние."""
        description = f"**ID:** `{rule.id}`\n**Имя:** `{rule.name}`\n**Тип:** `{rule.trigger_type}`"
        fields = []
        # Статус вкл/выкл
        if hasattr(rule, 'enabled'):
            fields.append({"name": "Статус", "value": f"{'Включено' if rule.enabled else 'Выключено'}", "inline": True})
        if rule.creator:
            fields.append({"name": "Изменил", "value": f"{rule.creator.mention} ({rule.creator.id})", "inline": True})
        if rule.trigger_metadata:
            fields.append({"name": "Условия", "value": f"{rule.trigger_metadata}", "inline": False})
        if rule.actions:
            actions = ", ".join([str(a.type) for a in rule.actions])
            fields.append({"name": "Действия", "value": actions, "inline": False})
        if getattr(rule, 'exempt_roles', None):
            fields.append({"name": "Исключённые роли", "value": ", ".join(r.mention for r in rule.exempt_roles), "inline": False})
        if getattr(rule, 'exempt_channels', None):
            fields.append({"name": "Исключённые каналы", "value": ", ".join(f"<#{c.id}>" for c in rule.exempt_channels), "inline": False})
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.UNKNOWN} AutoMod: правило изменено",
            description=description, fields=fields, guild=channel.guild,
        )

    async def log_automod_rule_delete(self, channel: discord.TextChannel, rule: discord.AutoModRule):
        description = f"**ID:** `{rule.id}`\n**Имя:** `{rule.name}`\n**Тип:** `{rule.trigger_type}`"
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.ERROR} AutoMod: правило удалено",
            description=description, fields=[], guild=channel.guild,
        )

    async def log_automod_action(self, channel: discord.TextChannel, execution: discord.AutoModAction):
        description = f"**ID правила:** `{execution.rule_id}`\n**Тип действия:** `{execution.action.type}`"
        fields = []
        if hasattr(execution, 'user_id'):
            fields.append({"name": "Пользователь", "value": f"<@{execution.user_id}> ({execution.user_id})", "inline": True})
        if hasattr(execution, 'channel_id'):
            fields.append({"name": "Канал", "value": f"<#{execution.channel_id}> ({execution.channel_id})", "inline": True})
        if hasattr(execution, 'content') and execution.content:
            fields.append({"name": "Контент", "value": f"```{execution.content[:1024]}```", "inline": False})
        if hasattr(execution, 'matched_keyword') and execution.matched_keyword:
            fields.append({"name": "Совпадение", "value": f"{execution.matched_keyword}", "inline": True})
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.ERROR} AutoMod: сработало правило",
            description=description, fields=fields, guild=channel.guild,
        )
