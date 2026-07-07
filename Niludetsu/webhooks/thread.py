import discord
from ..tools.Emojis import Emojis
from Niludetsu.locale import _

from Niludetsu.webhooks.base import BaseLogger

class ThreadLogger(BaseLogger):
    """Логгер для тредов (с детализацией Sapphire: archive/unarchive/lock/unlock)."""

    _THREAD_TYPES = {
        discord.ChannelType.public_thread: "thread_type_public",
        discord.ChannelType.private_thread: "thread_type_private",
        discord.ChannelType.news_thread: "thread_type_news",
    }

    def _get_thread_type(self, thread: discord.Thread, t) -> str:
        key = self._THREAD_TYPES.get(thread.type, "thread_type_unknown")
        return t("audit_log", key)

    async def log_thread_create(self, channel: discord.TextChannel, thread: discord.Thread):
        t = _(guild_id=thread.guild.id, bot=self.bot)
        description = (
            f"**{t('audit_log', 'field_thread')}:** {thread.mention} (`{thread.id}`)\n"
            f"**{t('audit_log', 'field_name')}:** `{thread.name}`\n"
            f"**{t('audit_log', 'field_parent')}:** {thread.parent.mention} (`{thread.parent.id}`)\n"
            f"**{t('audit_log', 'created_by')}:** {thread.owner.mention if thread.owner else t('audit_log', 'unknown')} ({thread.owner.id if thread.owner else 'N/A'})\n"
            f"**{t('audit_log', 'field_thread_type')}:** `{self._get_thread_type(thread, t)}`"
        )
        fields = []
        if thread.slowmode_delay:
            fields.append({"name": f"> {t('audit_log', 'field_slowmode_label')}", "value": f"`{t('audit_log', 'field_slowmode_value', count=thread.slowmode_delay)}`", "inline": False})
        if thread.auto_archive_duration:
            fields.append({"name": f"> {t('audit_log', 'field_auto_archive_label')}", "value": f"`{t('audit_log', 'field_auto_archive_value', count=thread.auto_archive_duration)}`", "inline": False})
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.SUCCESS} {t('audit_log', 'thread_create_title')}",
            description=description, fields=fields, guild=thread.guild,
        )

    async def log_thread_update(self, channel: discord.TextChannel, before: discord.Thread, after: discord.Thread):
        t = _(guild_id=after.guild.id, bot=self.bot)
        description = f"**{t('audit_log', 'field_thread')}:** {after.mention} (`{after.id}`)"
        fields = []
        if before.name != after.name:
            fields.append({"name": t('audit_log', 'field_name'), "value": f"`{before.name}` ➜ `{after.name}`", "inline": False})
        if before.archived != after.archived:
            status = t('audit_log', 'thread_archived') if after.archived else t('audit_log', 'thread_unarchived')
            fields.append({"name": t('audit_log', 'field_thread_status'), "value": f"`{status}`", "inline": False})
        if before.locked != after.locked:
            status = t('audit_log', 'thread_locked') if after.locked else t('audit_log', 'thread_unlocked')
            fields.append({"name": t('audit_log', 'field_thread_access'), "value": f"`{status}`", "inline": False})
        if before.slowmode_delay != after.slowmode_delay:
            fields.append({"name": t('audit_log', 'field_slowmode'), "value": f"`{before.slowmode_delay} сек.` ➜ `{after.slowmode_delay} сек.`", "inline": False})
        if before.auto_archive_duration != after.auto_archive_duration:
            fields.append({"name": t('audit_log', 'field_auto_archive'), "value": f"`{before.auto_archive_duration} мин.` ➜ `{after.auto_archive_duration} мин.`", "inline": False})
        if not fields:
            return
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.UNKNOWN} {t('audit_log', 'thread_update_title')}",
            description=description, fields=fields, guild=after.guild,
        )

    async def log_thread_delete(self, channel: discord.TextChannel, thread: discord.Thread):
        t = _(guild_id=thread.guild.id, bot=self.bot)
        description = (
            f"**{t('audit_log', 'field_name')}:** `{thread.name}`\n**{t('audit_log', 'field_id')}:** `{thread.id}`\n"
            f"**{t('audit_log', 'field_parent')}:** {thread.parent.mention} (`{thread.parent.id}`)\n"
            f"**{t('audit_log', 'field_thread_type')}:** `{self._get_thread_type(thread, t)}`"
        )
        if getattr(thread, 'message_count', None) is not None:
            description += f"\n**{t('audit_log', 'field_thread_messages')}:** `{thread.message_count}`"
        if getattr(thread, 'member_count', None) is not None:
            description += f"\n**{t('audit_log', 'field_thread_members')}:** `{thread.member_count}`"
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.ERROR} {t('audit_log', 'thread_delete_title')}",
            description=description, guild=thread.guild,
        )

    async def log_thread_member_join(self, channel: discord.TextChannel, member: discord.ThreadMember):
        """Участник присоединился к треду."""
        t = _(guild_id=(member.thread.guild.id if member.thread else channel.guild.id), bot=self.bot)
        thread = member.thread
        description = (
            f"**{t('audit_log', 'field_user')}:** <@{member.id}> (`{member.id}`)\n"
            f"**{t('audit_log', 'field_thread')}:** {thread.mention if thread else t('audit_log', 'unknown')} (`{thread.id if thread else 'N/A'}`)"
        )
        if thread and thread.parent:
            description += f"\n**{t('audit_log', 'field_parent')}:** {thread.parent.mention}"
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.SUCCESS} {t('audit_log', 'thread_join_title')}",
            description=description,
            guild=thread.guild if thread else channel.guild,
        )

    async def log_thread_member_remove(self, channel: discord.TextChannel, member: discord.ThreadMember):
        """Участник покинул тред."""
        t = _(guild_id=(member.thread.guild.id if member.thread else channel.guild.id), bot=self.bot)
        thread = member.thread
        description = (
            f"**{t('audit_log', 'field_user')}:** <@{member.id}> (`{member.id}`)\n"
            f"**{t('audit_log', 'field_thread')}:** {thread.mention if thread else t('audit_log', 'unknown')} (`{thread.id if thread else 'N/A'}`)"
        )
        if thread and thread.parent:
            description += f"\n**{t('audit_log', 'field_parent')}:** {thread.parent.mention}"
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.ERROR} {t('audit_log', 'thread_leave_title')}",
            description=description,
            guild=thread.guild if thread else channel.guild,
        )
