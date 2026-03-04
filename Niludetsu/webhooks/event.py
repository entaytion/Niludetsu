import discord, os
from datetime import datetime
from Niludetsu import Emojis
from Niludetsu.development.Webhooks import Webhooks

class EventLogger:
    """
    Логгер для событий Discord Scheduled Events через вебхук (максимум информации).
    """
    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.webhooks = Webhooks(bot)

    async def log_scheduled_event_create(self, channel: discord.TextChannel, event: discord.ScheduledEvent):
        title = f"{Emojis.SUCCESS} Событие: создано"
        description = f"**ID:** `{event.id}`\n**Название:** `{event.name}`"
        fields = []
        if event.creator:
            fields.append({"name": "Создатель", "value": f"{event.creator.mention} ({event.creator.id})", "inline": True})
        fields.append({"name": "Начало", "value": f"<t:{int(event.start_time.timestamp())}:F>", "inline": True})
        if event.end_time:
            fields.append({"name": "Конец", "value": f"<t:{int(event.end_time.timestamp())}:F>", "inline": True})
        # Доп. сведения
        fields.append({"name": "Тип", "value": f"`{getattr(event.entity_type, 'name', event.entity_type)}`", "inline": True})
        fields.append({"name": "Статус", "value": f"`{getattr(event.status, 'name', event.status)}`", "inline": True})
        fields.append({"name": "Приватность", "value": f"`{getattr(event.privacy_level, 'name', event.privacy_level)}`", "inline": True})
        # Канал/Локация
        ev_channel = getattr(event, 'channel', None)
        if ev_channel:
            fields.append({"name": "Канал", "value": ev_channel.mention, "inline": True})
        if getattr(event, 'location', None):
            fields.append({"name": "Локация", "value": f"`{event.location}`", "inline": True})
        if getattr(event, 'user_count', None) is not None:
            fields.append({"name": "Подписчики", "value": f"`{event.user_count}`", "inline": True})
        if hasattr(event, 'url'):
            fields.append({"name": "Ссылка", "value": f"{event.url}", "inline": False})

        # Длинное описание — во вложение
        file = None
        temp_filename = None
        if event.description:
            if len(event.description) <= 1024:
                fields.append({"name": "Описание", "value": f"```{event.description}```", "inline": False})
            else:
                now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                temp_filename = f"event_{event.id}_{now}.txt"
                try:
                    with open(temp_filename, 'w', encoding='utf-8') as f:
                        f.write(event.description)
                    file = discord.File(temp_filename, filename=temp_filename)
                    fields.append({"name": "Описание", "value": "Слишком длинное — см. вложение.", "inline": False})
                except Exception:
                    fields.append({"name": "Описание", "value": f"```{event.description[:1024]}```", "inline": False})

        try:
            await self.webhooks.send_log(
                channel=channel,
                title=title,
                description=description,
                fields=fields,
                thumbnail_url=event.cover_image.url if getattr(event, 'cover_image', None) else None,
                guild=channel.guild,
                file=file
            )
        finally:
            if temp_filename:
                try:
                    os.remove(temp_filename)
                except Exception:
                    pass

    async def log_scheduled_event_delete(self, channel: discord.TextChannel, event: discord.ScheduledEvent):
        title = f"{Emojis.ERROR} Событие: удалено"
        description = f"**ID:** `{event.id}`\n**Название:** `{event.name}`"
        fields = []
        if event.creator:
            fields.append({"name": "Создатель", "value": f"{event.creator.mention} ({event.creator.id})", "inline": True})
        await self.webhooks.send_log(
            channel=channel,
            title=title,
            description=description,
            fields=fields,
            thumbnail_url=event.cover_image.url if getattr(event, 'cover_image', None) else None,
            guild=channel.guild
        )

    async def log_scheduled_event_update(self, channel: discord.TextChannel, before: discord.ScheduledEvent, after: discord.ScheduledEvent):
        title = f"{Emojis.UNKNOWN} Событие: изменено"
        description = f"**ID:** `{after.id}`\n**Название:** `{after.name}`"
        fields = []
        if after.creator:
            fields.append({"name": "Создатель", "value": f"{after.creator.mention} ({after.creator.id})", "inline": True})
        # Изменения
        if before.name != after.name:
            fields.append({"name": "Название", "value": f"`{before.name}` ➜ `{after.name}`", "inline": False})
        # Описание с фолбэком во вложение
        file = None
        temp_filename = None
        if before.description != after.description:
            before_text = before.description or '[Не указано]'
            after_text = after.description or '[Не указано]'
            if len(before_text) <= 1024 and len(after_text) <= 1024:
                fields.append({"name": "Описание", "value": "Изменено", "inline": False})
                fields.append({"name": "Было", "value": f"```{before_text}```", "inline": False})
                fields.append({"name": "Стало", "value": f"```{after_text}```", "inline": False})
            else:
                now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                temp_filename = f"event_edit_{after.id}_{now}.txt"
                try:
                    with open(temp_filename, 'w', encoding='utf-8') as f:
                        f.write("Было:\n")
                        f.write(before_text)
                        f.write("\n\nСтало:\n")
                        f.write(after_text)
                    file = discord.File(temp_filename, filename=temp_filename)
                    fields.append({"name": "Описание", "value": "Изменено — подробности во вложении.", "inline": False})
                except Exception:
                    fields.append({"name": "Описание", "value": "Изменено (усечено)", "inline": False})
                    fields.append({"name": "Было", "value": f"```{before_text[:1024]}```", "inline": False})
                    fields.append({"name": "Стало", "value": f"```{after_text[:1024]}```", "inline": False})
        if before.location != after.location:
            fields.append({"name": "Локация", "value": f"`{before.location or 'Не указана'}` ➜ `{after.location or 'Не указана'}`", "inline": False})
        if before.status != after.status:
            fields.append({"name": "Статус", "value": f"`{before.status}` ➜ `{after.status}`", "inline": False})
        if before.entity_type != after.entity_type:
            fields.append({"name": "Тип", "value": f"`{before.entity_type}` ➜ `{after.entity_type}`", "inline": False})
        if before.start_time != after.start_time:
            fields.append({"name": "Время начала", "value": f"<t:{int(before.start_time.timestamp())}:F> ➜ <t:{int(after.start_time.timestamp())}:F>", "inline": False})
        if before.end_time != after.end_time:
            before_time = f"<t:{int(before.end_time.timestamp())}:F>" if before.end_time else "`Не указано`"
            after_time = f"<t:{int(after.end_time.timestamp())}:F>" if after.end_time else "`Не указано`"
            fields.append({"name": "Время окончания", "value": f"{before_time} ➜ {after_time}", "inline": False})
        if before.privacy_level != after.privacy_level:
            fields.append({"name": "Приватность", "value": f"`{before.privacy_level}` ➜ `{after.privacy_level}`", "inline": False})
        if getattr(before, 'cover_image', None) != getattr(after, 'cover_image', None):
            fields.append({"name": "Изображение", "value": "Изменено", "inline": False})
        if getattr(before, 'channel_id', None) != getattr(after, 'channel_id', None):
            fields.append({"name": "Канал", "value": f"`{before.channel_id or '—'}` ➜ `{after.channel_id or '—'}`", "inline": False})
        if not fields:
            return
        try:
            await self.webhooks.send_log(
                channel=channel,
                title=title,
                description=description,
                fields=fields,
                thumbnail_url=after.cover_image.url if getattr(after, 'cover_image', None) else None,
                guild=channel.guild,
                file=file
            )
        finally:
            if temp_filename:
                try:
                    os.remove(temp_filename)
                except Exception:
                    pass

    async def log_scheduled_event_add(self, channel: discord.TextChannel, event: discord.ScheduledEvent, user: discord.User):
        title = f"{Emojis.SUCCESS} Событие: пользователь присоединился"
        description = f"**ID события:** `{event.id}`\n**Название:** `{event.name}`"
        fields = [{"name": "Пользователь", "value": f"{user.mention} ({user.id})", "inline": False}]
        await self.webhooks.send_log(
            channel=channel,
            title=title,
            description=description,
            fields=fields,
            thumbnail_url=user.display_avatar.url,
            guild=channel.guild
        )

    async def log_scheduled_event_remove(self, channel: discord.TextChannel, event: discord.ScheduledEvent, user: discord.User):
        title = f"{Emojis.ERROR} Событие: пользователь покинул"
        description = f"**ID события:** `{event.id}`\n**Название:** `{event.name}`"
        fields = [{"name": "Пользователь", "value": f"{user.mention} ({user.id})", "inline": False}]
        await self.webhooks.send_log(
            channel=channel,
            title=title,
            description=description,
            fields=fields,
            thumbnail_url=user.display_avatar.url,
            guild=channel.guild
        ) 

