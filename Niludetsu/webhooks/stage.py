import discord
from Niludetsu import Emojis
from Niludetsu.webhooks.base import BaseLogger


class StageLogger(BaseLogger):
    """Логгер для трибун (Stage Instance) — создание, удаление, обновление, спикеры."""

    async def log_stage_create(self, channel: discord.TextChannel, stage_instance: discord.StageInstance):
        description = (
            f"**ID:** `{stage_instance.id}`\n"
            f"**Канал:** {stage_instance.channel.mention} (`{stage_instance.channel.id}`)\n"
            f"**Тема:** `{stage_instance.topic}`\n"
            f"**Приватность:** `{stage_instance.privacy_level.name}`\n"
            f"**Обнаружение отключено:** `{'Да' if stage_instance.discoverable_disabled else 'Нет'}`"
        )
        fields = []
        if stage_instance.scheduled_event:
            fields.append({"name": "Запланированное событие", "value": f"`{stage_instance.scheduled_event.name}`", "inline": False})
        # Количество участников
        if hasattr(stage_instance.channel, 'members'):
            fields.append({"name": "Участников в канале", "value": f"`{len(stage_instance.channel.members)}`", "inline": True})
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.SUCCESS} Трибуна: создана",
            description=description, fields=fields, guild=stage_instance.guild,
        )

    async def log_stage_delete(self, channel: discord.TextChannel, stage_instance: discord.StageInstance):
        description = (
            f"**ID:** `{stage_instance.id}`\n"
            f"**Канал:** {stage_instance.channel.mention} (`{stage_instance.channel.id}`)\n"
            f"**Тема:** `{stage_instance.topic}`"
        )
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.ERROR} Трибуна: удалена",
            description=description, guild=stage_instance.guild,
        )

    async def log_stage_update(self, channel: discord.TextChannel, before: discord.StageInstance, after: discord.StageInstance):
        description = f"**ID:** `{after.id}`\n**Канал:** {after.channel.mention} (`{after.channel.id}`)"
        fields = []
        if before.topic != after.topic:
            fields.append({"name": "Тема", "value": f"`{before.topic}` ➜ `{after.topic}`", "inline": False})
        if before.privacy_level != after.privacy_level:
            fields.append({"name": "Приватность", "value": f"`{before.privacy_level.name}` ➜ `{after.privacy_level.name}`", "inline": False})
        if before.discoverable_disabled != after.discoverable_disabled:
            fields.append({"name": "Обнаружение", "value": f"`{'Выкл' if before.discoverable_disabled else 'Вкл'}` ➜ `{'Выкл' if after.discoverable_disabled else 'Вкл'}`", "inline": False})
        if getattr(before, 'scheduled_event', None) != getattr(after, 'scheduled_event', None):
            fields.append({"name": "Событие", "value": f"`{getattr(before, 'scheduled_event', None)}` ➜ `{getattr(after, 'scheduled_event', None)}`", "inline": False})
        if not fields:
            return
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.UNKNOWN} Трибуна: обновлена",
            description=description, fields=fields, guild=after.guild,
        )

    async def log_stage_speaker_join(self, channel: discord.TextChannel, member: discord.Member, stage_channel: discord.StageChannel):
        """Спикер вышел на трибуну."""
        description = (
            f"**Пользователь:** {member.mention} (`{member.id}`)\n"
            f"**Канал:** {stage_channel.mention} (`{stage_channel.id}`)"
        )
        if hasattr(stage_channel, 'instance') and stage_channel.instance:
            description += f"\n**Тема:** `{stage_channel.instance.topic}`"
        fields = []
        if hasattr(stage_channel, 'members'):
            fields.append({"name": "Участников в канале", "value": f"`{len(stage_channel.members)}`", "inline": True})
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.SUCCESS} Трибуна: спикер присоединился",
            description=description, fields=fields,
            thumbnail_url=member.display_avatar.url, guild=member.guild,
        )

    async def log_stage_speaker_leave(self, channel: discord.TextChannel, member: discord.Member, stage_channel: discord.StageChannel):
        """Спикер покинул трибуну."""
        description = (
            f"**Пользователь:** {member.mention} (`{member.id}`)\n"
            f"**Канал:** {stage_channel.mention} (`{stage_channel.id}`)"
        )
        if hasattr(stage_channel, 'instance') and stage_channel.instance:
            description += f"\n**Тема:** `{stage_channel.instance.topic}`"
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.ERROR} Трибуна: спикер покинул",
            description=description,
            thumbnail_url=member.display_avatar.url, guild=member.guild,
        )

    async def log_stage_request_to_speak(self, channel: discord.TextChannel, member: discord.Member, stage_channel: discord.StageChannel):
        """Запрос на выступление на трибуне."""
        description = (
            f"**Пользователь:** {member.mention} (`{member.id}`)\n"
            f"**Канал:** {stage_channel.mention} (`{stage_channel.id}`)"
        )
        if hasattr(stage_channel, 'instance') and stage_channel.instance:
            description += f"\n**Тема:** `{stage_channel.instance.topic}`"
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.UNKNOWN} Трибуна: запрос на выступление",
            description=description,
            thumbnail_url=member.display_avatar.url, guild=member.guild,
        )

    async def log_stage_audience_join(self, channel: discord.TextChannel, member: discord.Member, stage_channel: discord.StageChannel):
        """Слушатель присоединился к трибуне."""
        description = (
            f"**Пользователь:** {member.mention} (`{member.id}`)\n"
            f"**Канал:** {stage_channel.mention} (`{stage_channel.id}`)"
        )
        if hasattr(stage_channel, 'instance') and stage_channel.instance:
            description += f"\n**Тема:** `{stage_channel.instance.topic}`"
        fields = []
        if hasattr(stage_channel, 'members'):
            fields.append({"name": "Участников в канале", "value": f"`{len(stage_channel.members)}`", "inline": True})
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.SUCCESS} Трибуна: слушатель присоединился",
            description=description, fields=fields,
            thumbnail_url=member.display_avatar.url, guild=member.guild,
        )
