import discord
from ..tools.Emojis import Emojis

from Niludetsu.webhooks.base import BaseLogger

class MessageLogger(BaseLogger):
    """Логгер для событий сообщений (удаление, редактирование, массовое удаление)."""

    async def log_message_delete(self, channel: discord.TextChannel, message: discord.Message):
        title = f"{Emojis.ERROR} Сообщение: удалено"
        description = (
            f"**Автор:** {message.author.mention} (`{message.author.id}`)\n"
            f"**Канал:** {message.channel.mention}\n"
            f"**ID:** `{message.id}`\n"
            f"**Jump:** [Перейти]({message.jump_url})\n"
            f"**Время:** <t:{int(message.created_at.timestamp())}:R>"
        )
        fields = []
        file = None
        temp_path = None
        if message.content:
            if len(message.content) <= 1024:
                fields.append({"name": "Содержимое", "value": f"```{message.content}```", "inline": False})
            else:
                try:
                    file, temp_path = self._temp_file(message.content, prefix=f"msg_{message.id}_")
                    fields.append({"name": "Содержимое", "value": "Превышает 1024 символов — см. вложенный файл.", "inline": False})
                except Exception:
                    fields.append({"name": "Содержимое", "value": f"```{message.content[:1024]}```", "inline": False})
        if message.attachments:
            attach_list = [f"[{a.filename}]({a.url})" for a in message.attachments]
            fields.append({"name": "Вложения", "value": "\n".join(attach_list), "inline": False})
        try:
            await self.webhooks.send_log(
                channel=channel, title=title, description=description,
                fields=fields if fields else None, file=file, guild=message.guild,
            )
        finally:
            self._cleanup(temp_path)

    async def log_message_bulk_delete(self, channel: discord.TextChannel, messages: list):
        title = f"{Emojis.ERROR} Сообщения: массовое удаление"
        description = f"**Канал:** {channel.mention}\n**Количество:** `{len(messages)}`"
        users = {msg.author.id for msg in messages if hasattr(msg, 'author') and msg.author}
        description += f"\n**Уникальных пользователей:** `{len(users)}`"

        # Формируем файл с логом
        lines = []
        for msg in messages:
            author_obj = getattr(msg, 'author', None)
            author = f"{author_obj or 'Неизвестно'} ({author_obj.id if author_obj else 'N/A'})"
            time_str = msg.created_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(msg, 'created_at') else 'N/A'
            content = getattr(msg, 'content', None) or '[Нет содержимого]'
            lines.append(f"{time_str} | {author}: {content}")
            if getattr(msg, 'attachments', None):
                for a in msg.attachments:
                    lines.append(f"[Вложение] {a.filename}: {a.url}")

        file, temp_path = self._temp_file('\n'.join(lines), prefix=f"bulk_{channel.id}_")

        # Краткая сводка
        preview = []
        for msg in messages[:5]:
            author_obj = getattr(msg, 'author', None)
            author = f"{author_obj or 'Неизвестно'}"
            content = getattr(msg, 'content', None) or '[Нет содержимого]'
            if len(content) > 50:
                content = content[:47] + '...'
            preview.append(f"- {author}: {content}")
        if len(messages) > 5:
            preview.append(f"... и еще {len(messages) - 5} сообщений (см. файл)")
        fields = []
        if preview:
            fields.append({"name": "Удаленные сообщения", "value": "\n".join(preview), "inline": False})
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
        title = f"{Emojis.UNKNOWN} Сообщение: изменено"
        description = (
            f"**Автор:** {before.author.mention} (`{before.author.id}`)\n"
            f"**Канал:** {before.channel.mention}\n"
            f"**ID:** `{before.id}`\n"
            f"**Jump:** [Перейти]({before.jump_url})\n"
            f"**Время:** <t:{int(before.created_at.timestamp())}:R>"
        )
        fields = []
        file = None
        temp_path = None
        if before.content != after.content:
            before_text = before.content or '[Нет содержимого]'
            after_text = after.content or '[Нет содержимого]'
            if len(before_text) <= 1024 and len(after_text) <= 1024:
                fields.append({"name": "Было", "value": f"```{before_text}```", "inline": False})
                fields.append({"name": "Стало", "value": f"```{after_text}```", "inline": False})
            else:
                try:
                    content = f"Было:\n{before_text}\n\nСтало:\n{after_text}"
                    file, temp_path = self._temp_file(content, prefix=f"edit_{before.id}_")
                    fields.append({"name": "Изменение содержимого", "value": "Содержимое слишком длинное — подробности во вложении.", "inline": False})
                except Exception:
                    fields.append({"name": "Было", "value": f"```{before_text[:1024]}```", "inline": False})
                    fields.append({"name": "Стало", "value": f"```{after_text[:1024]}```", "inline": False})
        if before.attachments != after.attachments:
            before_attachments = [f"[{a.filename}]({a.url})" for a in before.attachments]
            after_attachments = [f"[{a.filename}]({a.url})" for a in after.attachments]
            fields.append({"name": "Вложения были", "value": "\n".join(before_attachments) if before_attachments else '—', "inline": False})
            fields.append({"name": "Вложения стали", "value": "\n".join(after_attachments) if after_attachments else '—', "inline": False})
        try:
            await self.webhooks.send_log(
                channel=channel, title=title, description=description,
                fields=fields if fields else None, file=file, guild=before.guild,
            )
        finally:
            self._cleanup(temp_path)

    async def log_message_publish(self, channel: discord.TextChannel, message: discord.Message):
        """Сообщение опубликовано (crosspost) из канала новостей."""
        description = (
            f"**Автор:** {message.author.mention} (`{message.author.id}`)\n"
            f"**Канал:** {message.channel.mention}\n"
            f"**ID:** `{message.id}`\n"
            f"**Jump:** [Перейти]({message.jump_url})\n"
            f"**Время:** <t:{int(message.created_at.timestamp())}:R>"
        )
        fields = []
        if message.content:
            content = message.content[:1024] if len(message.content) > 1024 else message.content
            fields.append({"name": "Содержимое", "value": f"```{content}```", "inline": False})
        if message.attachments:
            attach_list = [f"[{a.filename}]({a.url})" for a in message.attachments]
            fields.append({"name": "Вложения", "value": "\n".join(attach_list), "inline": False})
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.SUCCESS} Сообщение: опубликовано (crosspost)",
            description=description, fields=fields, guild=message.guild,
        )
