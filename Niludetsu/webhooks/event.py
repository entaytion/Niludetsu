import discord
from Niludetsu import Emojis
from Niludetsu.webhooks.base import BaseLogger


class EventLogger(BaseLogger):
    """Логгер для Scheduled Events."""

    async def log_scheduled_event_create(self, channel: discord.TextChannel, event: discord.ScheduledEvent):
        description = f"**ID:** `{event.id}`\n**Название:** `{event.name}`"
        fields = []
        if event.creator:
            fields.append({"name": "Создатель", "value": f"{event.creator.mention} ({event.creator.id})", "inline": True})
        fields.append({"name": "Начало", "value": f"<t:{int(event.start_time.timestamp())}:F>", "inline": True})
        if event.end_time:
            fields.append({"name": "Конец", "value": f"<t:{int(event.end_time.timestamp())}:F>", "inline": True})
        fields.append({"name": "Тип", "value": f"`{getattr(event.entity_type, 'name', event.entity_type)}`", "inline": True})
        fields.append({"name": "Статус", "value": f"`{getattr(event.status, 'name', event.status)}`", "inline": True})
        fields.append({"name": "Приватность", "value": f"`{getattr(event.privacy_level, 'name', event.privacy_level)}`", "inline": True})
        ev_channel = getattr(event, 'channel', None)
        if ev_channel:
            fields.append({"name": "Канал", "value": ev_channel.mention, "inline": True})
        if getattr(event, 'location', None):
            fields.append({"name": "Локация", "value": f"`{event.location}`", "inline": True})
        if hasattr(event, 'url'):
            fields.append({"name": "Ссылка", "value": f"{event.url}", "inline": False})
        # Описание — в файл если длинное
        file, temp_path = None, None
        if event.description:
            if len(event.description) <= 1024:
                fields.append({"name": "Описание", "value": f"```{event.description}```", "inline": False})
            else:
                try:
                    file, temp_path = self._temp_file(event.description, prefix=f"event_{event.id}_")
                    fields.append({"name": "Описание", "value": "Слишком длинное — см. вложение.", "inline": False})
                except Exception:
                    fields.append({"name": "Описание", "value": f"```{event.description[:1024]}```", "inline": False})
        try:
            await self.webhooks.send_log(
                channel=channel, title=f"{Emojis.SUCCESS} Событие: создано",
                description=description, fields=fields,
                thumbnail_url=event.cover_image.url if getattr(event, 'cover_image', None) else None,
                guild=channel.guild, file=file,
            )
        finally:
            self._cleanup(temp_path)

    async def log_scheduled_event_delete(self, channel: discord.TextChannel, event: discord.ScheduledEvent):
        description = f"**ID:** `{event.id}`\n**Название:** `{event.name}`"
        fields = []
        if event.creator:
            fields.append({"name": "Создатель", "value": f"{event.creator.mention} ({event.creator.id})", "inline": True})
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.ERROR} Событие: удалено",
            description=description, fields=fields,
            thumbnail_url=event.cover_image.url if getattr(event, 'cover_image', None) else None,
            guild=channel.guild,
        )

    async def log_scheduled_event_update(self, channel: discord.TextChannel, before: discord.ScheduledEvent, after: discord.ScheduledEvent):
        description = f"**ID:** `{after.id}`\n**Название:** `{after.name}`"
        fields = []
        if after.creator:
            fields.append({"name": "Создатель", "value": f"{after.creator.mention} ({after.creator.id})", "inline": True})
        if before.name != after.name:
            fields.append({"name": "Название", "value": f"`{before.name}` ➜ `{after.name}`", "inline": False})
        if before.location != after.location:
            fields.append({"name": "Локация", "value": f"`{before.location or 'Не указана'}` ➜ `{after.location or 'Не указана'}`", "inline": False})
        if before.status != after.status:
            fields.append({"name": "Статус", "value": f"`{before.status}` ➜ `{after.status}`", "inline": False})
        if before.entity_type != after.entity_type:
            fields.append({"name": "Тип", "value": f"`{before.entity_type}` ➜ `{after.entity_type}`", "inline": False})
        if before.start_time != after.start_time:
            fields.append({"name": "Начало", "value": f"<t:{int(before.start_time.timestamp())}:F> ➜ <t:{int(after.start_time.timestamp())}:F>", "inline": False})
        if before.end_time != after.end_time:
            bt = f"<t:{int(before.end_time.timestamp())}:F>" if before.end_time else "`Не указано`"
            at = f"<t:{int(after.end_time.timestamp())}:F>" if after.end_time else "`Не указано`"
            fields.append({"name": "Конец", "value": f"{bt} ➜ {at}", "inline": False})
        if before.privacy_level != after.privacy_level:
            fields.append({"name": "Приватность", "value": f"`{before.privacy_level}` ➜ `{after.privacy_level}`", "inline": False})
        if getattr(before, 'cover_image', None) != getattr(after, 'cover_image', None):
            fields.append({"name": "Изображение", "value": "Изменено", "inline": False})
        # Описание
        file, temp_path = None, None
        if before.description != after.description:
            bd = before.description or '[Не указано]'
            ad = after.description or '[Не указано]'
            if len(bd) <= 1024 and len(ad) <= 1024:
                fields.append({"name": "Описание (было)", "value": f"```{bd}```", "inline": False})
                fields.append({"name": "Описание (стало)", "value": f"```{ad}```", "inline": False})
            else:
                try:
                    file, temp_path = self._temp_file(f"Было:\n{bd}\n\nСтало:\n{ad}", prefix=f"event_edit_{after.id}_")
                    fields.append({"name": "Описание", "value": "Изменено — подробности во вложении.", "inline": False})
                except Exception:
                    fields.append({"name": "Описание", "value": "Изменено (усечено)", "inline": False})
        if len(fields) <= 1:  # Только creator, нет реальных изменений
            return
        try:
            await self.webhooks.send_log(
                channel=channel, title=f"{Emojis.UNKNOWN} Событие: изменено",
                description=description, fields=fields,
                thumbnail_url=after.cover_image.url if getattr(after, 'cover_image', None) else None,
                guild=channel.guild, file=file,
            )
        finally:
            self._cleanup(temp_path)

    async def log_scheduled_event_add(self, channel: discord.TextChannel, event: discord.ScheduledEvent, user: discord.User):
        description = f"**ID события:** `{event.id}`\n**Название:** `{event.name}`"
        fields = [{"name": "Пользователь", "value": f"{user.mention} ({user.id})", "inline": False}]
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.SUCCESS} Событие: пользователь присоединился",
            description=description, fields=fields,
            thumbnail_url=user.display_avatar.url, guild=channel.guild,
        )

    async def log_scheduled_event_remove(self, channel: discord.TextChannel, event: discord.ScheduledEvent, user: discord.User):
        description = f"**ID события:** `{event.id}`\n**Название:** `{event.name}`"
        fields = [{"name": "Пользователь", "value": f"{user.mention} ({user.id})", "inline": False}]
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.ERROR} Событие: пользователь покинул",
            description=description, fields=fields,
            thumbnail_url=user.display_avatar.url, guild=channel.guild,
        )
