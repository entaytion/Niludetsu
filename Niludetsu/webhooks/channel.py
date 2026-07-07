import discord
from ..tools.Emojis import Emojis

from Niludetsu.locale import _
from Niludetsu.webhooks.base import BaseLogger
from Niludetsu.webhooks.constants import PERMISSION_NAMES

class ChannelLogger(BaseLogger):
    """Логгер для событий каналов (создание, удаление, обновление, пермишены, пины)."""

    async def log_channel_create(self, log_channel: discord.TextChannel, channel: discord.abc.GuildChannel, creator: discord.User = None):
        t = _(guild_id=channel.guild.id, bot=self.bot)
        description = f"**{t('audit_log', 'field_id')}:** `{channel.id}`\n**{t('audit_log', 'field_name')}:** `{channel.name}`\n**{t('audit_log', 'field_type')}:** `{str(channel.type)}`"
        if channel.category:
            description += f"\n**{t('audit_log', 'field_category')}:** `{channel.category.name}`"
        if not creator:
            creator = await self._safe_audit_log(channel.guild, discord.AuditLogAction.channel_create, channel.id)
        if creator:
            description += f"\n**{t('audit_log', 'created_by')}** {creator.mention} ({creator.id})"
        await self.webhooks.send_log(
            channel=log_channel, title=f"{Emojis.SUCCESS} {t('audit_log', 'channel_create_title')}",
            description=description, fields=[], guild=channel.guild,
        )

    async def log_channel_delete(self, log_channel: discord.TextChannel, channel: discord.abc.GuildChannel, remover: discord.User = None):
        t = _(guild_id=channel.guild.id, bot=self.bot)
        description = f"**{t('audit_log', 'field_id')}:** `{channel.id}`\n**{t('audit_log', 'field_name')}:** `{channel.name}`\n**{t('audit_log', 'field_type')}:** `{str(channel.type)}`"
        if channel.category:
            description += f"\n**{t('audit_log', 'field_category')}:** `{channel.category.name}`"
        if not remover:
            remover = await self._safe_audit_log(channel.guild, discord.AuditLogAction.channel_delete, channel.id)
        if remover:
            description += f"\n**{t('audit_log', 'deleted_by')}** {remover.mention} ({remover.id})"
        await self.webhooks.send_log(
            channel=log_channel, title=f"{Emojis.ERROR} {t('audit_log', 'channel_delete_title')}",
            description=description, fields=[], guild=channel.guild,
        )

    async def log_channel_update(self, log_channel: discord.TextChannel, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        """Полное сравнение каналов — покрывает все поля из Sapphire."""
        t = _(guild_id=after.guild.id, bot=self.bot)
        none_label = t('audit_log', 'none')
        on_label = t('audit_log', 'on')
        off_label = t('audit_log', 'off')
        no_limit_label = t('audit_log', 'no_limit')
        auto_label = t('audit_log', 'auto')

        changes = []

        # --- Основные поля ---
        if before.name != after.name:
            changes.append(f"**{t('audit_log', 'field_name')}:** `{before.name}` → `{after.name}`")
        if before.category != after.category:
            changes.append(f"**{t('audit_log', 'field_category')}:** `{before.category.name if before.category else none_label}` → `{after.category.name if after.category else none_label}`")
        # Channel Type Update
        if before.type != after.type:
            changes.append(f"**{t('audit_log', 'field_type')}:** `{before.type}` → `{after.type}`")

        # --- Текстовые каналы ---
        if hasattr(before, 'topic') and hasattr(after, 'topic') and before.topic != after.topic:
            changes.append(f"**{t('audit_log', 'field_topic')}:** `{before.topic or none_label}` → `{after.topic or none_label}`")
        if hasattr(before, 'nsfw') and hasattr(after, 'nsfw') and before.nsfw != after.nsfw:
            changes.append(f"**{t('audit_log', 'field_nsfw')}:** `{on_label if after.nsfw else off_label}`")
        if hasattr(before, 'slowmode_delay') and hasattr(after, 'slowmode_delay') and before.slowmode_delay != after.slowmode_delay:
            changes.append(f"**{t('audit_log', 'field_slowmode')}:** `{self._format_slowmode(before.slowmode_delay)}` → `{self._format_slowmode(after.slowmode_delay)}`")

        # --- Голосовые каналы ---
        if hasattr(before, 'bitrate') and hasattr(after, 'bitrate') and before.bitrate != after.bitrate:
            changes.append(f"**{t('audit_log', 'field_bitrate')}:** `{before.bitrate // 1000}kbps` → `{after.bitrate // 1000}kbps`")
        if hasattr(before, 'user_limit') and hasattr(after, 'user_limit') and before.user_limit != after.user_limit:
            bl = no_limit_label if before.user_limit == 0 else str(before.user_limit)
            al = no_limit_label if after.user_limit == 0 else str(after.user_limit)
            changes.append(f"**{t('audit_log', 'field_user_limit')}:** `{bl}` → `{al}`")
        # RTC Region
        if hasattr(before, 'rtc_region') and hasattr(after, 'rtc_region') and before.rtc_region != after.rtc_region:
            changes.append(f"**{t('audit_log', 'field_rtc_region')}:** `{before.rtc_region or auto_label}` → `{after.rtc_region or auto_label}`")
        # Video Quality
        if hasattr(before, 'video_quality_mode') and hasattr(after, 'video_quality_mode') and before.video_quality_mode != after.video_quality_mode:
            changes.append(f"**{t('audit_log', 'field_video_quality')}:** `{before.video_quality_mode}` → `{after.video_quality_mode}`")

        # --- Форум/тред настройки ---
        if hasattr(before, 'default_auto_archive_duration') and hasattr(after, 'default_auto_archive_duration'):
            if before.default_auto_archive_duration != after.default_auto_archive_duration:
                changes.append(f"**{t('audit_log', 'field_auto_archive')}:** `{before.default_auto_archive_duration}мин` → `{after.default_auto_archive_duration}мин`")
        if hasattr(before, 'default_thread_slowmode_delay') and hasattr(after, 'default_thread_slowmode_delay'):
            if before.default_thread_slowmode_delay != after.default_thread_slowmode_delay:
                changes.append(f"**{t('audit_log', 'field_slowmode_threads')}:** `{self._format_slowmode(before.default_thread_slowmode_delay)}` → `{self._format_slowmode(after.default_thread_slowmode_delay)}`")
        # Default Reaction Emoji
        if hasattr(before, 'default_reaction_emoji') and hasattr(after, 'default_reaction_emoji'):
            if before.default_reaction_emoji != after.default_reaction_emoji:
                changes.append(f"**{t('audit_log', 'field_default_emoji')}:** `{before.default_reaction_emoji or none_label}` → `{after.default_reaction_emoji or none_label}`")
        # Default Sort Order
        if hasattr(before, 'default_sort_order') and hasattr(after, 'default_sort_order'):
            if before.default_sort_order != after.default_sort_order:
                changes.append(f"**{t('audit_log', 'field_sort_order')}:** `{before.default_sort_order}` → `{after.default_sort_order}`")
        # Forum Tags
        if hasattr(before, 'available_tags') and hasattr(after, 'available_tags'):
            before_tags = {tag.name for tag in (before.available_tags or [])}
            after_tags = {tag.name for tag in (after.available_tags or [])}
            if before_tags != after_tags:
                added = after_tags - before_tags
                removed = before_tags - after_tags
                parts = []
                if added:
                    parts.append(f"+{', '.join(added)}")
                if removed:
                    parts.append(f"-{', '.join(removed)}")
                changes.append(f"**{t('audit_log', 'field_forum_tags')}:** {'; '.join(parts)}")
        # Forum Layout
        if hasattr(before, 'default_layout') and hasattr(after, 'default_layout'):
            if before.default_layout != after.default_layout:
                changes.append(f"**{t('audit_log', 'field_forum_layout')}:** `{before.default_layout}` → `{after.default_layout}`")

        # Если изменилась только позиция — пропускаем
        if not changes:
            return

        # Получаем модератора
        updater = await self._safe_audit_log(after.guild, discord.AuditLogAction.channel_update, after.id)

        description = f"**{t('audit_log', 'field_id')}:** `{after.id}`\n**{t('audit_log', 'field_name')}:** `{after.name}`\n**{t('audit_log', 'field_type')}:** `{str(after.type)}`"
        if after.category:
            description += f"\n**{t('audit_log', 'field_category')}:** `{after.category.name}`"
        if updater:
            description += f"\n**{t('audit_log', 'updated_by')}** {updater.mention} ({updater.id})"

        fields = [{"name": t('audit_log', 'field_change_field'), "value": c, "inline": False} for c in changes]
        await self.webhooks.send_log(
            channel=log_channel, title=f"{Emojis.UNKNOWN} {t('audit_log', 'channel_update_title')}",
            description=description, fields=fields, guild=after.guild,
        )

    async def log_permissions_update(self, log_channel: discord.TextChannel, channel: discord.TextChannel, moderator: discord.Member, changes: list):
        t = _(guild_id=channel.guild.id, bot=self.bot)
        description = f"{t('audit_log', 'field_perms_channel')}: `{channel.id}`\n{t('audit_log', 'field_perms_channel_name')}: {channel.mention}\n{t('audit_log', 'field_perms_moderator')}: {moderator.mention} ({moderator.id})"
        fields = []
        for change in changes:
            role = change.get("role")
            perms = change.get("permissions", {})
            role_name = role.mention if hasattr(role, 'mention') else str(role)
            role_id = getattr(role, 'id', None)
            value = f"{t('audit_log', 'field_perms_role')}: {role_name} {(f'({role_id})' if role_id else '')}\n"
            for perm, diff in perms.items():
                before = diff.get("before")
                after = diff.get("after")
                perm_name = PERMISSION_NAMES.get(perm, perm)
                value += f"- {perm_name}: {'✅' if before else '❌'} → {'✅' if after else '❌'}\n"
            fields.append({"name": t('audit_log', 'field_perms_update'), "value": value, "inline": False})
        await self.webhooks.send_log(
            channel=log_channel, title=f"{Emojis.UNKNOWN} {t('audit_log', 'field_perms_title')}",
            description=description, fields=fields, guild=channel.guild,
        )

    async def log_pins_update(self, log_channel: discord.TextChannel, last_pin=None):
        """Пины: обновлены (раньше был в PinsLogger — теперь тут)."""
        t = _(guild_id=log_channel.guild.id, bot=self.bot)
        description = f"**{t('audit_log', 'field_channel')}:** {log_channel.mention} ({log_channel.id})"
        fields = []
        if last_pin:
            fields.append({
                "name": t('audit_log', 'field_pins_last'),
                "value": f"[{t('audit_log', 'jump')}]({last_pin.jump_url})\n{t('audit_log', 'field_author')}: {last_pin.author.mention} ({last_pin.author.id})\n{t('audit_log', 'field_time')}: <t:{int(last_pin.created_at.timestamp())}:F>",
                "inline": False,
            })
        await self.webhooks.send_log(
            channel=log_channel, title=f"{Emojis.UNKNOWN} {t('audit_log', 'field_pins_title')}",
            description=description, fields=fields, guild=log_channel.guild,
        )

    @staticmethod
    def _format_slowmode(seconds: int) -> str:
        if seconds == 0:
            return "Выкл"
        if seconds < 60:
            return f"{seconds}с"
        if seconds < 3600:
            m, s = divmod(seconds, 60)
            return f"{m}м {s}с" if s else f"{m}м"
        h, remainder = divmod(seconds, 3600)
        m = remainder // 60
        return f"{h}ч {m}м" if m else f"{h}ч"
