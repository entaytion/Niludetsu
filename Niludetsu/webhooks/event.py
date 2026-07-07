import discord
from ..tools.Emojis import Emojis
from Niludetsu.locale import _

from Niludetsu.webhooks.base import BaseLogger


class EventLogger(BaseLogger):
    """Логгер для Scheduled Events."""

    async def log_scheduled_event_create(self, channel: discord.TextChannel, event: discord.ScheduledEvent):
        t = _(guild_id=channel.guild.id, bot=self.bot)
        description = f"**ID:** `{event.id}`\n**{t('audit_log', 'field_event_name')}:** `{event.name}`"
        fields = []
        if event.creator:
            fields.append({"name": t('audit_log', 'created_by'), "value": f"{event.creator.mention} ({event.creator.id})", "inline": True})
        fields.append({"name": t('audit_log', 'field_event_start'), "value": f"<t:{int(event.start_time.timestamp())}:F>", "inline": True})
        if event.end_time:
            fields.append({"name": t('audit_log', 'field_event_end'), "value": f"<t:{int(event.end_time.timestamp())}:F>", "inline": True})
        fields.append({"name": t('audit_log', 'field_type'), "value": f"`{getattr(event.entity_type, 'name', event.entity_type)}`", "inline": True})
        fields.append({"name": t('audit_log', 'field_event_status'), "value": f"`{getattr(event.status, 'name', event.status)}`", "inline": True})
        fields.append({"name": t('audit_log', 'field_stage_privacy'), "value": f"`{getattr(event.privacy_level, 'name', event.privacy_level)}`", "inline": True})
        ev_channel = getattr(event, 'channel', None)
        if ev_channel:
            fields.append({"name": t('audit_log', 'field_channel'), "value": ev_channel.mention, "inline": True})
        if getattr(event, 'location', None):
            fields.append({"name": t('audit_log', 'field_event_location'), "value": f"`{event.location}`", "inline": True})
        if hasattr(event, 'url'):
            fields.append({"name": t('audit_log', 'field_event_link'), "value": f"{event.url}", "inline": False})
        file, temp_path = None, None
        if event.description:
            if len(event.description) <= 1024:
                fields.append({"name": t('audit_log', 'field_event_desc'), "value": f"```{event.description}```", "inline": False})
            else:
                try:
                    file, temp_path = self._temp_file(event.description, prefix=f"event_{event.id}_")
                    fields.append({"name": t('audit_log', 'field_event_desc'), "value": t('audit_log', 'event_desc_too_long_file'), "inline": False})
                except Exception:
                    fields.append({"name": t('audit_log', 'field_event_desc'), "value": f"```{event.description[:1024]}```", "inline": False})
        try:
            await self.webhooks.send_log(
                channel=channel, title=f"{Emojis.SUCCESS} {t('audit_log', 'event_create_title')}",
                description=description, fields=fields,
                thumbnail_url=event.cover_image.url if getattr(event, 'cover_image', None) else None,
                guild=channel.guild, file=file,
            )
        finally:
            self._cleanup(temp_path)

    async def log_scheduled_event_delete(self, channel: discord.TextChannel, event: discord.ScheduledEvent):
        t = _(guild_id=channel.guild.id, bot=self.bot)
        description = f"**ID:** `{event.id}`\n**{t('audit_log', 'field_event_name')}:** `{event.name}`"
        fields = []
        if event.creator:
            fields.append({"name": t('audit_log', 'created_by'), "value": f"{event.creator.mention} ({event.creator.id})", "inline": True})
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.ERROR} {t('audit_log', 'event_delete_title')}",
            description=description, fields=fields,
            thumbnail_url=event.cover_image.url if getattr(event, 'cover_image', None) else None,
            guild=channel.guild,
        )

    async def log_scheduled_event_update(self, channel: discord.TextChannel, before: discord.ScheduledEvent, after: discord.ScheduledEvent):
        t = _(guild_id=channel.guild.id, bot=self.bot)
        description = f"**ID:** `{after.id}`\n**{t('audit_log', 'field_event_name')}:** `{after.name}`"
        fields = []
        if after.creator:
            fields.append({"name": t('audit_log', 'created_by'), "value": f"{after.creator.mention} ({after.creator.id})", "inline": True})
        if before.name != after.name:
            fields.append({"name": t('audit_log', 'field_event_name'), "value": f"`{before.name}` ➜ `{after.name}`", "inline": False})
        if before.location != after.location:
            fields.append({"name": t('audit_log', 'field_event_location'), "value": f"`{before.location or t('audit_log', 'event_location_not_set')}` ➜ `{after.location or t('audit_log', 'event_location_not_set')}`", "inline": False})
        if before.status != after.status:
            fields.append({"name": t('audit_log', 'field_event_status'), "value": f"`{before.status}` ➜ `{after.status}`", "inline": False})
        if before.entity_type != after.entity_type:
            fields.append({"name": t('audit_log', 'field_type'), "value": f"`{before.entity_type}` ➜ `{after.entity_type}`", "inline": False})
        if before.start_time != after.start_time:
            fields.append({"name": t('audit_log', 'field_event_start'), "value": f"<t:{int(before.start_time.timestamp())}:F> ➜ <t:{int(after.start_time.timestamp())}:F>", "inline": False})
        if before.end_time != after.end_time:
            bt = f"<t:{int(before.end_time.timestamp())}:F>" if before.end_time else f"`{t('audit_log', 'event_not_specified')}`"
            at = f"<t:{int(after.end_time.timestamp())}:F>" if after.end_time else f"`{t('audit_log', 'event_not_specified')}`"
            fields.append({"name": t('audit_log', 'field_event_end'), "value": f"{bt} ➜ {at}", "inline": False})
        if before.privacy_level != after.privacy_level:
            fields.append({"name": t('audit_log', 'field_stage_privacy'), "value": f"`{before.privacy_level}` ➜ `{after.privacy_level}`", "inline": False})
        if getattr(before, 'cover_image', None) != getattr(after, 'cover_image', None):
            fields.append({"name": t('audit_log', 'field_event_image'), "value": t('audit_log', 'event_image_changed'), "inline": False})
        file, temp_path = None, None
        if before.description != after.description:
            bd = before.description or f'[{t("audit_log", "event_not_specified")}]'
            ad = after.description or f'[{t("audit_log", "event_not_specified")}]'
            if len(bd) <= 1024 and len(ad) <= 1024:
                fields.append({"name": t('audit_log', 'field_event_desc_was'), "value": f"```{bd}```", "inline": False})
                fields.append({"name": t('audit_log', 'field_event_desc_now'), "value": f"```{ad}```", "inline": False})
            else:
                try:
                    file, temp_path = self._temp_file(f"Было:\n{bd}\n\nСтало:\n{ad}", prefix=f"event_edit_{after.id}_")
                    fields.append({"name": t('audit_log', 'field_event_desc'), "value": t('audit_log', 'event_desc_too_long'), "inline": False})
                except Exception:
                    fields.append({"name": t('audit_log', 'field_event_desc'), "value": t('audit_log', 'event_desc_truncated'), "inline": False})
        if len(fields) <= 1:
            return
        try:
            await self.webhooks.send_log(
                channel=channel, title=f"{Emojis.UNKNOWN} {t('audit_log', 'event_update_title')}",
                description=description, fields=fields,
                thumbnail_url=after.cover_image.url if getattr(after, 'cover_image', None) else None,
                guild=channel.guild, file=file,
            )
        finally:
            self._cleanup(temp_path)

    async def log_scheduled_event_add(self, channel: discord.TextChannel, event: discord.ScheduledEvent, user: discord.User):
        t = _(guild_id=channel.guild.id, bot=self.bot)
        description = f"**ID события:** `{event.id}`\n**{t('audit_log', 'field_event_name')}:** `{event.name}`"
        fields = [{"name": t('audit_log', 'field_user'), "value": f"{user.mention} ({user.id})", "inline": False}]
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.SUCCESS} {t('audit_log', 'event_user_join')}",
            description=description, fields=fields,
            thumbnail_url=user.display_avatar.url, guild=channel.guild,
        )

    async def log_scheduled_event_remove(self, channel: discord.TextChannel, event: discord.ScheduledEvent, user: discord.User):
        t = _(guild_id=channel.guild.id, bot=self.bot)
        description = f"**ID события:** `{event.id}`\n**{t('audit_log', 'field_event_name')}:** `{event.name}`"
        fields = [{"name": t('audit_log', 'field_user'), "value": f"{user.mention} ({user.id})", "inline": False}]
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.ERROR} {t('audit_log', 'event_user_leave')}",
            description=description, fields=fields,
            thumbnail_url=user.display_avatar.url, guild=channel.guild,
        )
