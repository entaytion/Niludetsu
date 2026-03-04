import discord
from Niludetsu import Emojis
from Niludetsu.development.Webhooks import Webhooks

class AutoModLogger:
    """
    Логгер для событий AutoMod (автоматическая модерация) через вебхук.
    """
    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.webhooks = Webhooks(bot)

    async def log_automod_rule_create(self, channel: discord.TextChannel, rule: discord.AutoModRule):
        title = f"{Emojis.SUCCESS} AutoMod: правило создано"
        description = f"**ID:** `{rule.id}`\n**Имя:** `{rule.name}`\n**Тип:** `{rule.trigger_type}`"
        fields = []
        if rule.creator:
            fields.append({"name": "Создатель", "value": f"{rule.creator.mention} ({rule.creator.id})", "inline": True})
        if rule.trigger_metadata:
            fields.append({"name": "Условия", "value": f"{rule.trigger_metadata}", "inline": False})
        if rule.actions:
            actions = ", ".join([str(a.type) for a in rule.actions])
            fields.append({"name": "Действия", "value": actions, "inline": False})
        await self.webhooks.send_log(
            channel=channel,
            title=title,
            description=description,
            fields=fields,
            thumbnail_url=None,
            guild=channel.guild
        )

    async def log_automod_rule_update(self, channel: discord.TextChannel, rule: discord.AutoModRule):
        title = f"{Emojis.UNKNOWN} AutoMod: правило изменено"
        description = f"**ID:** `{rule.id}`\n**Имя:** `{rule.name}`\n**Тип:** `{rule.trigger_type}`"
        fields = []
        if rule.creator:
            fields.append({"name": "Изменил", "value": f"{rule.creator.mention} ({rule.creator.id})", "inline": True})
        if rule.trigger_metadata:
            fields.append({"name": "Условия", "value": f"{rule.trigger_metadata}", "inline": False})
        if rule.actions:
            actions = ", ".join([str(a.type) for a in rule.actions])
            fields.append({"name": "Действия", "value": actions, "inline": False})
        await self.webhooks.send_log(
            channel=channel,
            title=title,
            description=description,
            fields=fields,
            thumbnail_url=None,
            guild=channel.guild
        )

    async def log_automod_rule_delete(self, channel: discord.TextChannel, rule: discord.AutoModRule):
        title = f"{Emojis.ERROR} AutoMod: правило удалено"
        description = f"**ID:** `{rule.id}`\n**Имя:** `{rule.name}`\n**Тип:** `{rule.trigger_type}`"
        await self.webhooks.send_log(
            channel=channel,
            title=title,
            description=description,
            fields=[],
            thumbnail_url=None,
            guild=channel.guild
        )

    async def log_automod_action(self, channel: discord.TextChannel, execution: discord.AutoModAction):
        title = f"{Emojis.ERROR} AutoMod: сработало правило"
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
            channel=channel,
            title=title,
            description=description,
            fields=fields,
            thumbnail_url=None,
            guild=channel.guild
        ) 

