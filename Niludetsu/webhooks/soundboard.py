import discord
from ..tools.Emojis import Emojis

from Niludetsu.webhooks.base import BaseLogger

class SoundboardLogger(BaseLogger):
    """Логгер для событий Soundboard."""

    async def log_sound_create(self, channel: discord.TextChannel, sound):
        description = (
            f"**ID:** `{sound.id}`\n"
            f"**Название:** `{sound.name}`\n"
            f"**Эмодзи:** {sound.emoji if sound.emoji else '`Нет`'}\n"
            f"**Громкость:** `{int(sound.volume * 100)}%`\n"
            f"**Доступен:** `{'Да' if getattr(sound, 'available', True) else 'Нет'}`"
        )
        if getattr(sound, 'user', None):
            description += f"\n**Создатель:** {sound.user.mention} (`{sound.user.id}`)"
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.SUCCESS} Звук: добавлен",
            description=description,
            thumbnail_url=sound.user.display_avatar.url if getattr(sound, 'user', None) else None,
            guild=sound.guild if getattr(sound, 'guild', None) else None,
        )

    async def log_sound_delete(self, channel: discord.TextChannel, sound):
        description = (
            f"**ID:** `{sound.id}`\n**Название:** `{sound.name}`\n"
            f"**Эмодзи:** {sound.emoji if sound.emoji else '`Нет`'}"
        )
        if getattr(sound, 'user', None):
            description += f"\n**Создатель:** {sound.user.mention} (`{sound.user.id}`)"
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.ERROR} Звук: удален",
            description=description,
            thumbnail_url=sound.user.display_avatar.url if getattr(sound, 'user', None) else None,
            guild=sound.guild if getattr(sound, 'guild', None) else None,
        )

    async def log_sound_update(self, channel: discord.TextChannel, before, after):
        fields = []
        if before.name != after.name:
            fields.append({"name": "Название", "value": f"`{before.name}` ➜ `{after.name}`", "inline": False})
        if before.volume != after.volume:
            fields.append({"name": "Громкость", "value": f"`{int(before.volume * 100)}%` ➜ `{int(after.volume * 100)}%`", "inline": False})
        if before.emoji != after.emoji:
            fields.append({"name": "Эмодзи", "value": f"{before.emoji or '`Нет`'} ➜ {after.emoji or '`Нет`'}", "inline": False})
        if getattr(before, 'available', True) != getattr(after, 'available', True):
            fields.append({"name": "Доступен", "value": f"`{'Да' if getattr(before, 'available', True) else 'Нет'}` ➜ `{'Да' if getattr(after, 'available', True) else 'Нет'}`", "inline": False})
        if not fields:
            return
        description = f"**ID:** `{after.id}`\n**Название:** `{after.name}`"
        if getattr(after, 'user', None):
            description += f"\n**Создатель:** {after.user.mention} (`{after.user.id}`)"
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.UNKNOWN} Звук: обновлен",
            description=description, fields=fields,
            thumbnail_url=after.user.display_avatar.url if getattr(after, 'user', None) else None,
            guild=after.guild if getattr(after, 'guild', None) else None,
        )
