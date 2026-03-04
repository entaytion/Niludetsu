import discord
from Niludetsu import Emojis
from Niludetsu.development.Webhooks import Webhooks

class ThreadLogger:
    """
    Логгер для действий с тредами через вебхук (максимум информации).
    """
    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.webhooks = Webhooks(bot)

    def _get_thread_type(self, thread: discord.Thread) -> str:
        types = {
            discord.ChannelType.public_thread: "Публичный",
            discord.ChannelType.private_thread: "Приватный",
            discord.ChannelType.news_thread: "Новостной"
        }
        return types.get(thread.type, "Неизвестный")

    async def log_thread_create(self, channel: discord.TextChannel, thread: discord.Thread):
        title = f"{Emojis.SUCCESS} Тред: создан"
        description = f"**Тред:** {thread.mention} (`{thread.id}`)\n"
        description += f"**Название:** `{thread.name}`\n"
        description += f"**Родительский канал:** {thread.parent.mention} (`{thread.parent.id}`)\n"
        description += f"**Создатель:** {thread.owner.mention if thread.owner else 'Неизвестно'} ({thread.owner.id if thread.owner else 'N/A'})\n"
        description += f"**Тип треда:** `{self._get_thread_type(thread)}`"
        fields = []
        if thread.slowmode_delay:
            fields.append({
                "name": "> Медленный режим:",
                "value": f"`{thread.slowmode_delay} секунд`",
                "inline": False
            })
        if thread.auto_archive_duration:
            fields.append({
                "name": "> Автоархивация:",
                "value": f"`{thread.auto_archive_duration} минут`",
                "inline": False
            })
        await self.webhooks.send_log(
            channel=channel,
            title=title,
            description=description,
            fields=fields,
            guild=thread.guild
        )

    async def log_thread_update(self, channel: discord.TextChannel, before: discord.Thread, after: discord.Thread):
        title = f"{Emojis.UNKNOWN} Тред: обновлен"
        description = f"**Тред:** {after.mention} (`{after.id}`)"
        fields = []
        if before.name != after.name:
            fields.append({
                "name": "> Изменения:",
                "value": f"- Название: `{before.name}` ➜ `{after.name}`",
                "inline": False
            })
        if before.archived != after.archived:
            status = "Архивирован" if after.archived else "Разархивирован"
            fields.append({
                "name": "> Изменения:",
                "value": f"- Статус: `{status}`",
                "inline": False
            })
        if before.locked != after.locked:
            status = "Заблокирован" if after.locked else "Разблокирован"
            fields.append({
                "name": "> Изменения:",
                "value": f"- Доступ: `{status}`",
                "inline": False
            })
        if before.slowmode_delay != after.slowmode_delay:
            fields.append({
                "name": "> Изменения:",
                "value": f"- Медленный режим: `{before.slowmode_delay} сек.` ➜ `{after.slowmode_delay} сек.`",
                "inline": False
            })
        if before.auto_archive_duration != after.auto_archive_duration:
            fields.append({
                "name": "> Изменения:",
                "value": f"- Автоархивация: `{before.auto_archive_duration} мин.` ➜ `{after.auto_archive_duration} мин.`",
                "inline": False
            })
        if not fields:
            return
        await self.webhooks.send_log(
            channel=channel,
            title=title,
            description=description,
            fields=fields,
            guild=after.guild
        )

    async def log_thread_delete(self, channel: discord.TextChannel, thread: discord.Thread):
        title = f"{Emojis.ERROR} Тред: удален"
        description = f"**Название:** `{thread.name}`\n"
        description += f"**ID:** `{thread.id}`\n"
        description += f"**Родительский канал:** {thread.parent.mention} (`{thread.parent.id}`)\n"
        description += f"**Тип треда:** `{self._get_thread_type(thread)}`"
        await self.webhooks.send_log(
            channel=channel,
            title=title,
            description=description,
            guild=thread.guild
        ) 

