import discord
from ..tools.Emojis import Emojis

from Niludetsu.webhooks.base import BaseLogger
from Niludetsu.webhooks.constants import PERMISSION_NAMES

class ChannelLogger(BaseLogger):
    """Логгер для событий каналов (создание, удаление, обновление, пермишены, пины)."""

    async def log_channel_create(self, log_channel: discord.TextChannel, channel: discord.abc.GuildChannel, creator: discord.User = None):
        description = f"**ID:** `{channel.id}`\n**Название:** `{channel.name}`\n**Тип:** `{str(channel.type)}`"
        if channel.category:
            description += f"\n**Категория:** `{channel.category.name}`"
        if not creator:
            creator = await self._safe_audit_log(channel.guild, discord.AuditLogAction.channel_create, channel.id)
        if creator:
            description += f"\n**Создатель:** {creator.mention} ({creator.id})"
        await self.webhooks.send_log(
            channel=log_channel, title=f"{Emojis.SUCCESS} Канал: создан",
            description=description, fields=[], guild=channel.guild,
        )

    async def log_channel_delete(self, log_channel: discord.TextChannel, channel: discord.abc.GuildChannel, remover: discord.User = None):
        description = f"**ID:** `{channel.id}`\n**Название:** `{channel.name}`\n**Тип:** `{str(channel.type)}`"
        if channel.category:
            description += f"\n**Категория:** `{channel.category.name}`"
        if not remover:
            remover = await self._safe_audit_log(channel.guild, discord.AuditLogAction.channel_delete, channel.id)
        if remover:
            description += f"\n**Удалил:** {remover.mention} ({remover.id})"
        await self.webhooks.send_log(
            channel=log_channel, title=f"{Emojis.ERROR} Канал: удалён",
            description=description, fields=[], guild=channel.guild,
        )

    async def log_channel_update(self, log_channel: discord.TextChannel, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        """Полное сравнение каналов — покрывает все поля из Sapphire."""
        changes = []

        # --- Основные поля ---
        if before.name != after.name:
            changes.append(f"**Название:** `{before.name}` → `{after.name}`")
        if before.category != after.category:
            changes.append(f"**Категория:** `{before.category.name if before.category else 'Нет'}` → `{after.category.name if after.category else 'Нет'}`")
        # Channel Type Update
        if before.type != after.type:
            changes.append(f"**Тип:** `{before.type}` → `{after.type}`")

        # --- Текстовые каналы ---
        if hasattr(before, 'topic') and hasattr(after, 'topic') and before.topic != after.topic:
            changes.append(f"**Тема:** `{before.topic or 'Нет'}` → `{after.topic or 'Нет'}`")
        if hasattr(before, 'nsfw') and hasattr(after, 'nsfw') and before.nsfw != after.nsfw:
            changes.append(f"**NSFW:** `{'Вкл' if after.nsfw else 'Выкл'}`")
        if hasattr(before, 'slowmode_delay') and hasattr(after, 'slowmode_delay') and before.slowmode_delay != after.slowmode_delay:
            changes.append(f"**Медленный режим:** `{self._format_slowmode(before.slowmode_delay)}` → `{self._format_slowmode(after.slowmode_delay)}`")

        # --- Голосовые каналы ---
        if hasattr(before, 'bitrate') and hasattr(after, 'bitrate') and before.bitrate != after.bitrate:
            changes.append(f"**Битрейт:** `{before.bitrate // 1000}kbps` → `{after.bitrate // 1000}kbps`")
        if hasattr(before, 'user_limit') and hasattr(after, 'user_limit') and before.user_limit != after.user_limit:
            bl = 'Без лимита' if before.user_limit == 0 else str(before.user_limit)
            al = 'Без лимита' if after.user_limit == 0 else str(after.user_limit)
            changes.append(f"**Лимит пользователей:** `{bl}` → `{al}`")
        # RTC Region
        if hasattr(before, 'rtc_region') and hasattr(after, 'rtc_region') and before.rtc_region != after.rtc_region:
            changes.append(f"**RTC регион:** `{before.rtc_region or 'Авто'}` → `{after.rtc_region or 'Авто'}`")
        # Video Quality
        if hasattr(before, 'video_quality_mode') and hasattr(after, 'video_quality_mode') and before.video_quality_mode != after.video_quality_mode:
            changes.append(f"**Качество видео:** `{before.video_quality_mode}` → `{after.video_quality_mode}`")

        # --- Форум/тред настройки ---
        if hasattr(before, 'default_auto_archive_duration') and hasattr(after, 'default_auto_archive_duration'):
            if before.default_auto_archive_duration != after.default_auto_archive_duration:
                changes.append(f"**Авто-архивация по умолчанию:** `{before.default_auto_archive_duration}мин` → `{after.default_auto_archive_duration}мин`")
        if hasattr(before, 'default_thread_slowmode_delay') and hasattr(after, 'default_thread_slowmode_delay'):
            if before.default_thread_slowmode_delay != after.default_thread_slowmode_delay:
                changes.append(f"**Slowmode тредов:** `{self._format_slowmode(before.default_thread_slowmode_delay)}` → `{self._format_slowmode(after.default_thread_slowmode_delay)}`")
        # Default Reaction Emoji
        if hasattr(before, 'default_reaction_emoji') and hasattr(after, 'default_reaction_emoji'):
            if before.default_reaction_emoji != after.default_reaction_emoji:
                changes.append(f"**Дефолтный эмодзи реакции:** `{before.default_reaction_emoji or 'Нет'}` → `{after.default_reaction_emoji or 'Нет'}`")
        # Default Sort Order
        if hasattr(before, 'default_sort_order') and hasattr(after, 'default_sort_order'):
            if before.default_sort_order != after.default_sort_order:
                changes.append(f"**Порядок сортировки:** `{before.default_sort_order}` → `{after.default_sort_order}`")
        # Forum Tags
        if hasattr(before, 'available_tags') and hasattr(after, 'available_tags'):
            before_tags = {t.name for t in (before.available_tags or [])}
            after_tags = {t.name for t in (after.available_tags or [])}
            if before_tags != after_tags:
                added = after_tags - before_tags
                removed = before_tags - after_tags
                parts = []
                if added:
                    parts.append(f"+{', '.join(added)}")
                if removed:
                    parts.append(f"-{', '.join(removed)}")
                changes.append(f"**Теги форума:** {'; '.join(parts)}")
        # Forum Layout
        if hasattr(before, 'default_layout') and hasattr(after, 'default_layout'):
            if before.default_layout != after.default_layout:
                changes.append(f"**Макет форума:** `{before.default_layout}` → `{after.default_layout}`")

        # Если изменилась только позиция — пропускаем
        if not changes:
            return

        # Получаем модератора
        updater = await self._safe_audit_log(after.guild, discord.AuditLogAction.channel_update, after.id)

        description = f"**ID:** `{after.id}`\n**Название:** `{after.name}`\n**Тип:** `{str(after.type)}`"
        if after.category:
            description += f"\n**Категория:** `{after.category.name}`"
        if updater:
            description += f"\n**Обновил:** {updater.mention} ({updater.id})"

        fields = [{"name": "Изменение", "value": c, "inline": False} for c in changes]
        await self.webhooks.send_log(
            channel=log_channel, title=f"{Emojis.UNKNOWN} Канал: изменён",
            description=description, fields=fields, guild=after.guild,
        )

    async def log_permissions_update(self, log_channel: discord.TextChannel, channel: discord.TextChannel, moderator: discord.Member, changes: list):
        description = f"ID канала: `{channel.id}`\nКанал: {channel.mention}\nМодератор: {moderator.mention} ({moderator.id})"
        fields = []
        for change in changes:
            role = change.get("role")
            perms = change.get("permissions", {})
            role_name = role.mention if hasattr(role, 'mention') else str(role)
            role_id = getattr(role, 'id', None)
            value = f"Роли: {role_name} {(f'({role_id})' if role_id else '')}\n"
            for perm, diff in perms.items():
                before = diff.get("before")
                after = diff.get("after")
                perm_name = PERMISSION_NAMES.get(perm, perm)
                value += f"- {perm_name}: {'✅' if before else '❌'} → {'✅' if after else '❌'}\n"
            fields.append({"name": "Изменения прав доступа:", "value": value, "inline": False})
        await self.webhooks.send_log(
            channel=log_channel, title=f"{Emojis.UNKNOWN} Изменены права доступа в канале",
            description=description, fields=fields, guild=channel.guild,
        )

    async def log_pins_update(self, log_channel: discord.TextChannel, last_pin=None):
        """Пины: обновлены (раньше был в PinsLogger — теперь тут)."""
        description = f"**Канал:** {log_channel.mention} ({log_channel.id})"
        fields = []
        if last_pin:
            fields.append({
                "name": "Последний пин",
                "value": f"[Перейти к сообщению]({last_pin.jump_url})\nАвтор: {last_pin.author.mention} ({last_pin.author.id})\nВремя: <t:{int(last_pin.created_at.timestamp())}:F>",
                "inline": False,
            })
        await self.webhooks.send_log(
            channel=log_channel, title=f"{Emojis.UNKNOWN} Пины: обновлены",
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
