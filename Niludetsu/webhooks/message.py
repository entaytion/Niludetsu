import discord, os
from datetime import datetime
from Niludetsu import Emojis
from Niludetsu.development.Webhooks import Webhooks

class MessageLogger:
    """
    Логгер для событий сообщений через вебхук (удаление, редактирование, массовое удаление).
    """
    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.webhooks = Webhooks(bot)

    async def log_message_delete(self, channel: discord.TextChannel, message: discord.Message):
        title = f"{Emojis.ERROR} Сообщение: удалено"
        description = f"**Автор:** {message.author.mention} (`{message.author.id}`)\n"
        description += f"**Канал:** {message.channel.mention}\n"
        description += f"**ID:** `{message.id}`\n"
        description += f"**Jump:** [Перейти]({message.jump_url})\n"
        description += f"**Время:** <t:{int(message.created_at.timestamp())}:R>"
        fields = []
        file = None
        temp_filename = None
        if message.content:
            if len(message.content) <= 1024:
                fields.append({"name": "Содержимое", "value": f"```{message.content}```", "inline": False})
            else:
                # Содержимое превышает лимит поля эмбеда — сохраняем в файл и прикрепляем
                now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                temp_filename = f"message_{message.id}_{now}.txt"
                try:
                    with open(temp_filename, 'w', encoding='utf-8') as f:
                        f.write(message.content)
                    file = discord.File(temp_filename, filename=temp_filename)
                    fields.append({
                        "name": "Содержимое",
                        "value": "Превышает 1024 символов — см. вложенный файл.",
                        "inline": False
                    })
                except Exception:
                    # В случае ошибки записи файла — добавим усеченное содержимое
                    fields.append({"name": "Содержимое", "value": f"```{message.content[:1024]}```", "inline": False})
        if message.attachments:
            attach_list = [f"[{a.filename}]({a.url})" for a in message.attachments]
            fields.append({"name": "Вложения", "value": "\n".join(attach_list), "inline": False})
        try:
            await self.webhooks.send_log(
                channel=channel,
                title=title,
                description=description,
                fields=fields if fields else None,
                file=file,
                guild=message.guild
            )
        finally:
            if temp_filename:
                try:
                    os.remove(temp_filename)
                except Exception:
                    pass

    async def log_message_bulk_delete(self, channel: discord.TextChannel, messages: list):
        title = f"{Emojis.ERROR} Сообщения: массовое удаление"
        description = f"**Канал:** {channel.mention}\n**Количество:** `{len(messages)}`"
        users = set()
        for msg in messages:
            if hasattr(msg, 'author') and msg.author:
                users.add(msg.author.id)
        description += f"\n**Уникальных пользователей:** `{len(users)}`"
        # Формируем файл с логом
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"deleted_messages_{channel.id}_{now}.txt"
        lines = []
        for msg in messages:
            author_obj = getattr(msg, 'author', None)
            author = f"{author_obj or 'Неизвестно'} ({author_obj.id if author_obj else 'N/A'})"
            time = msg.created_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(msg, 'created_at') else 'N/A'
            content = getattr(msg, 'content', None) or '[Нет содержимого]'
            lines.append(f"{time} | {author}: {content}")
            if getattr(msg, 'attachments', None):
                for a in msg.attachments:
                    lines.append(f"[Вложение] {a.filename}: {a.url}")
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        file = discord.File(filename, filename=filename)
        # Краткая сводка
        preview = []
        for msg in messages[:5]:
            author_obj = getattr(msg, 'author', None)
            author = f"{author_obj or 'Неизвестно'} ({author_obj.id if author_obj else 'N/A'})"
            content = getattr(msg, 'content', None) or '[Нет содержимого]'
            if len(content) > 50:
                content = content[:47] + '...'
            preview.append(f"- {author}: {content}")
        if len(messages) > 5:
            preview.append(f"... и еще {len(messages) - 5} сообщений (см. файл)")
        fields = []
        if preview:
            fields.append({"name": "Удаленные сообщения", "value": "\n".join(preview), "inline": False})
        await self.webhooks.send_log(
            channel=channel,
            title=title,
            description=description,
            fields=fields if fields else None,
            file=file,
            guild=channel.guild
        )
        try:
            os.remove(filename)
        except Exception:
            pass

    async def log_message_edit(self, channel: discord.TextChannel, before: discord.Message, after: discord.Message):
        if before.content == after.content and before.attachments == after.attachments:
            return
        title = f"{Emojis.UNKNOWN} Сообщение: изменено"
        description = f"**Автор:** {before.author.mention} (`{before.author.id}`)\n"
        description += f"**Канал:** {before.channel.mention}\n"
        description += f"**ID:** `{before.id}`\n"
        description += f"**Jump:** [Перейти]({before.jump_url})\n"
        description += f"**Время:** <t:{int(before.created_at.timestamp())}:R>"
        fields = []
        file = None
        temp_filename = None
        if before.content != after.content:
            before_text = before.content or '[Нет содержимого]'
            after_text = after.content or '[Нет содержимого]'
            if len(before_text) <= 1024 and len(after_text) <= 1024:
                fields.append({"name": "Было", "value": f"```{before_text}```", "inline": False})
                fields.append({"name": "Стало", "value": f"```{after_text}```", "inline": False})
            else:
                # Один из текстов превышает лимит — сохраняем оба в файл
                now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                temp_filename = f"message_edit_{before.id}_{now}.txt"
                try:
                    with open(temp_filename, 'w', encoding='utf-8') as f:
                        f.write("Было:\n")
                        f.write(before_text)
                        f.write("\n\nСтало:\n")
                        f.write(after_text)
                    file = discord.File(temp_filename, filename=temp_filename)
                    fields.append({
                        "name": "Изменение содержимого",
                        "value": "Содержимое слишком длинное — подробности во вложении.",
                        "inline": False
                    })
                except Exception:
                    # Фолбек на усечение, если не удалось записать файл
                    fields.append({"name": "Было", "value": f"```{before_text[:1024]}```", "inline": False})
                    fields.append({"name": "Стало", "value": f"```{after_text[:1024]}```", "inline": False})
        if before.attachments != after.attachments:
            before_attachments = [f"[{a.filename}]({a.url})" for a in before.attachments]
            after_attachments = [f"[{a.filename}]({a.url})" for a in after.attachments]
            fields.append({"name": "Вложения были", "value": "\n".join(before_attachments) if before_attachments else '—', "inline": False})
            fields.append({"name": "Вложения стали", "value": "\n".join(after_attachments) if after_attachments else '—', "inline": False})
        try:
            await self.webhooks.send_log(
                channel=channel,
                title=title,
                description=description,
                fields=fields if fields else None,
                file=file,
                guild=before.guild
            )
        finally:
            if temp_filename:
                try:
                    os.remove(temp_filename)
                except Exception:
                    pass

