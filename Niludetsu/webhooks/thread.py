import discord
from ..tools.Emojis import Emojis

from Niludetsu.webhooks.base import BaseLogger

class ThreadLogger(BaseLogger):
    """Логгер для тредов (с детализацией Sapphire: archive/unarchive/lock/unlock)."""

    _THREAD_TYPES = {
        discord.ChannelType.public_thread: "Публичный",
        discord.ChannelType.private_thread: "Приватный",
        discord.ChannelType.news_thread: "Новостной",
    }

    def _get_thread_type(self, thread: discord.Thread) -> str:
        return self._THREAD_TYPES.get(thread.type, "Неизвестный")

    async def log_thread_create(self, channel: discord.TextChannel, thread: discord.Thread):
        description = (
            f"**Тред:** {thread.mention} (`{thread.id}`)\n"
            f"**Название:** `{thread.name}`\n"
            f"**Родительский канал:** {thread.parent.mention} (`{thread.parent.id}`)\n"
            f"**Создатель:** {thread.owner.mention if thread.owner else 'Неизвестно'} ({thread.owner.id if thread.owner else 'N/A'})\n"
            f"**Тип:** `{self._get_thread_type(thread)}`"
        )
        fields = []
        if thread.slowmode_delay:
            fields.append({"name": "> Медленный режим:", "value": f"`{thread.slowmode_delay} секунд`", "inline": False})
        if thread.auto_archive_duration:
            fields.append({"name": "> Автоархивация:", "value": f"`{thread.auto_archive_duration} минут`", "inline": False})
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.SUCCESS} Тред: создан",
            description=description, fields=fields, guild=thread.guild,
        )

    async def log_thread_update(self, channel: discord.TextChannel, before: discord.Thread, after: discord.Thread):
        description = f"**Тред:** {after.mention} (`{after.id}`)"
        fields = []
        if before.name != after.name:
            fields.append({"name": "Название", "value": f"`{before.name}` ➜ `{after.name}`", "inline": False})
        if before.archived != after.archived:
            status = "Архивирован" if after.archived else "Разархивирован"
            fields.append({"name": "Статус", "value": f"`{status}`", "inline": False})
        if before.locked != after.locked:
            status = "Заблокирован" if after.locked else "Разблокирован"
            fields.append({"name": "Доступ", "value": f"`{status}`", "inline": False})
        if before.slowmode_delay != after.slowmode_delay:
            fields.append({"name": "Медленный режим", "value": f"`{before.slowmode_delay} сек.` ➜ `{after.slowmode_delay} сек.`", "inline": False})
        if before.auto_archive_duration != after.auto_archive_duration:
            fields.append({"name": "Автоархивация", "value": f"`{before.auto_archive_duration} мин.` ➜ `{after.auto_archive_duration} мин.`", "inline": False})
        if not fields:
            return
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.UNKNOWN} Тред: обновлен",
            description=description, fields=fields, guild=after.guild,
        )

    async def log_thread_delete(self, channel: discord.TextChannel, thread: discord.Thread):
        description = (
            f"**Название:** `{thread.name}`\n**ID:** `{thread.id}`\n"
            f"**Родительский канал:** {thread.parent.mention} (`{thread.parent.id}`)\n"
            f"**Тип:** `{self._get_thread_type(thread)}`"
        )
        if getattr(thread, 'message_count', None) is not None:
            description += f"\n**Сообщений:** `{thread.message_count}`"
        if getattr(thread, 'member_count', None) is not None:
            description += f"\n**Участников:** `{thread.member_count}`"
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.ERROR} Тред: удален",
            description=description, guild=thread.guild,
        )

    async def log_thread_member_join(self, channel: discord.TextChannel, member: discord.ThreadMember):
        """Участник присоединился к треду."""
        thread = member.thread
        description = (
            f"**Пользователь:** <@{member.id}> (`{member.id}`)\n"
            f"**Тред:** {thread.mention if thread else 'Неизвестно'} (`{thread.id if thread else 'N/A'}`)"
        )
        if thread and thread.parent:
            description += f"\n**Родительский канал:** {thread.parent.mention}"
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.SUCCESS} Тред: участник присоединился",
            description=description,
            guild=thread.guild if thread else channel.guild,
        )

    async def log_thread_member_remove(self, channel: discord.TextChannel, member: discord.ThreadMember):
        """Участник покинул тред."""
        thread = member.thread
        description = (
            f"**Пользователь:** <@{member.id}> (`{member.id}`)\n"
            f"**Тред:** {thread.mention if thread else 'Неизвестно'} (`{thread.id if thread else 'N/A'}`)"
        )
        if thread and thread.parent:
            description += f"\n**Родительский канал:** {thread.parent.mention}"
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.ERROR} Тред: участник покинул",
            description=description,
            guild=thread.guild if thread else channel.guild,
        )
