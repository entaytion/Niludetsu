import discord
from ..tools.Emojis import Emojis

from Niludetsu.locale import _
from Niludetsu.webhooks.base import BaseLogger

class MessageLogger(BaseLogger):
    """Логгер для событий сообщений (удаление, редактирование, массовое удаление)."""

    async def log_message_delete(self, channel: discord.TextChannel, message: discord.Message):
        t = _(guild_id=message.guild.id, bot=self.bot)
        title = f"{Emojis.ERROR} {t('audit_log', 'msg_delete_title')}"
        description = (
            f"**{t('audit_log', 'field_author')}:** {message.author.mention} (`{message.author.id}`)\n"
            f"**{t('audit_log', 'field_channel')}:** {message.channel.mention}\n"
            f"**{t('audit_log', 'field_id')}:** `{message.id}`\n"
            f"**{t('audit_log', 'field_jump')}:** [{t('audit_log', 'jump')}]({message.jump_url})\n"
            f"**{t('audit_log', 'field_time')}:** <t:{int(message.created_at.timestamp())}:R>"
        )
        fields = []
        file = None
        temp_path = None
        if message.content:
            if len(message.content) <= 1024:
                fields.append({"name": t('audit_log', 'field_content'), "value": f"```{message.content}```", "inline": False})
            else:
                try:
                    file, temp_path = self._temp_file(message.content, prefix=f"msg_{message.id}_")
                    fields.append({"name": t('audit_log', 'field_content'), "value": t('audit_log', 'too_long_truncated'), "inline": False})
                except Exception:
                    fields.append({"name": t('audit_log', 'field_content'), "value": f"```{message.content[:1024]}```", "inline": False})
        if message.attachments:
            attach_list = [f"[{a.filename}]({a.url})" for a in message.attachments]
            fields.append({"name": t('audit_log', 'field_attachments'), "value": "\n".join(attach_list), "inline": False})
        try:
            await self.webhooks.send_log(
                channel=channel, title=title, description=description,
                fields=fields if fields else None, file=file, guild=message.guild,
            )
        finally:
            self._cleanup(temp_path)

    async def log_message_bulk_delete(self, channel: discord.TextChannel, messages: list):
        t = _(guild_id=channel.guild.id, bot=self.bot)
        title = f"{Emojis.ERROR} {t('audit_log', 'msg_bulk_delete_title')}"
        description = f"**{t('audit_log', 'field_channel')}:** {channel.mention}\n**{t('audit_log', 'field_bulk_count')}:** `{len(messages)}`"
        users = {msg.author.id for msg in messages if hasattr(msg, 'author') and msg.author}
        description += f"\n**{t('audit_log', 'field_bulk_users')}:** `{len(users)}`"

        # Формируем файл с логом
        lines = []
        for msg in messages:
            author_obj = getattr(msg, 'author', None)
            author = f"{author_obj or t('audit_log', 'unknown')} ({author_obj.id if author_obj else 'N/A'})"
            time_str = msg.created_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(msg, 'created_at') else 'N/A'
            content = getattr(msg, 'content', None) or t('audit_log', 'no_content')
            lines.append(f"{time_str} | {author}: {content}")
            if getattr(msg, 'attachments', None):
                for a in msg.attachments:
                    lines.append(f"[{t('audit_log', 'attachment')}] {a.filename}: {a.url}")

        file, temp_path = self._temp_file('\n'.join(lines), prefix=f"bulk_{channel.id}_")

        # Краткая сводка
        preview = []
        for msg in messages[:5]:
            author_obj = getattr(msg, 'author', None)
            author = f"{author_obj or t('audit_log', 'unknown')}"
            content = getattr(msg, 'content', None) or t('audit_log', 'no_content')
            if len(content) > 50:
                content = content[:47] + '...'
            preview.append(f"- {author}: {content}")
        if len(messages) > 5:
            preview.append(t('audit_log', 'and_more', count=len(messages) - 5))
        fields = []
        if preview:
            fields.append({"name": t('audit_log', 'field_bulk_deleted'), "value": "\n".join(preview), "inline": False})
        try:
            await self.webhooks.send_log(
                channel=channel, title=title, description=description,
                fields=fields if fields else None, file=file, guild=channel.guild,
            )
        finally:
            self._cleanup(temp_path)

    async def log_message_edit(self, channel: discord.TextChannel, before: discord.Message, after: discord.Message):
        if before.content == after.content and before.attachments == after.attachments:
            return
        t = _(guild_id=before.guild.id, bot=self.bot)
        title = f"{Emojis.UNKNOWN} {t('audit_log', 'msg_edit_title')}"
        description = (
            f"**{t('audit_log', 'field_author')}:** {before.author.mention} (`{before.author.id}`)\n"
            f"**{t('audit_log', 'field_channel')}:** {before.channel.mention}\n"
            f"**{t('audit_log', 'field_id')}:** `{before.id}`\n"
            f"**{t('audit_log', 'field_jump')}:** [{t('audit_log', 'jump')}]({before.jump_url})\n"
            f"**{t('audit_log', 'field_time')}:** <t:{int(before.created_at.timestamp())}:R>"
        )
        fields = []
        file = None
        temp_path = None
        if before.content != after.content:
            before_text = before.content or t('audit_log', 'no_content')
            after_text = after.content or t('audit_log', 'no_content')
            if len(before_text) <= 1024 and len(after_text) <= 1024:
                fields.append({"name": t('audit_log', 'was'), "value": f"```{before_text}```", "inline": False})
                fields.append({"name": t('audit_log', 'became'), "value": f"```{after_text}```", "inline": False})
            else:
                try:
                    content = f"{t('audit_log', 'was')}:\n{before_text}\n\n{t('audit_log', 'became')}:\n{after_text}"
                    file, temp_path = self._temp_file(content, prefix=f"edit_{before.id}_")
                    fields.append({"name": t('audit_log', 'field_content_change'), "value": t('audit_log', 'field_content_too_long'), "inline": False})
                except Exception:
                    fields.append({"name": t('audit_log', 'was'), "value": f"```{before_text[:1024]}```", "inline": False})
                    fields.append({"name": t('audit_log', 'became'), "value": f"```{after_text[:1024]}```", "inline": False})
        if before.attachments != after.attachments:
            before_attachments = [f"[{a.filename}]({a.url})" for a in before.attachments]
            after_attachments = [f"[{a.filename}]({a.url})" for a in after.attachments]
            fields.append({"name": t('audit_log', 'field_attach_was'), "value": "\n".join(before_attachments) if before_attachments else '—', "inline": False})
            fields.append({"name": t('audit_log', 'field_attach_became'), "value": "\n".join(after_attachments) if after_attachments else '—', "inline": False})
        try:
            await self.webhooks.send_log(
                channel=channel, title=title, description=description,
                fields=fields if fields else None, file=file, guild=before.guild,
            )
        finally:
            self._cleanup(temp_path)

    async def log_message_publish(self, channel: discord.TextChannel, message: discord.Message):
        """Сообщение опубликовано (crosspost) из канала новостей."""
        t = _(guild_id=message.guild.id, bot=self.bot)
        description = (
            f"**{t('audit_log', 'field_author')}:** {message.author.mention} (`{message.author.id}`)\n"
            f"**{t('audit_log', 'field_channel')}:** {message.channel.mention}\n"
            f"**{t('audit_log', 'field_id')}:** `{message.id}`\n"
            f"**{t('audit_log', 'field_jump')}:** [{t('audit_log', 'jump')}]({message.jump_url})\n"
            f"**{t('audit_log', 'field_time')}:** <t:{int(message.created_at.timestamp())}:R>"
        )
        fields = []
        if message.content:
            content = message.content[:1024] if len(message.content) > 1024 else message.content
            fields.append({"name": t('audit_log', 'field_content'), "value": f"```{content}```", "inline": False})
        if message.attachments:
            attach_list = [f"[{a.filename}]({a.url})" for a in message.attachments]
            fields.append({"name": t('audit_log', 'field_attachments'), "value": "\n".join(attach_list), "inline": False})
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.SUCCESS} {t('audit_log', 'msg_publish_title')}",
            description=description, fields=fields, guild=message.guild,
        )
