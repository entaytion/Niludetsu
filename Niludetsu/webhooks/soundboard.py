import discord
from ..tools.Emojis import Emojis
from Niludetsu.locale import _

from Niludetsu.webhooks.base import BaseLogger

class SoundboardLogger(BaseLogger):
    """Логгер для событий Soundboard."""

    async def log_sound_create(self, channel: discord.TextChannel, sound):
        guild = getattr(sound, 'guild', None)
        t = _(guild_id=guild.id, bot=self.bot) if guild else _(guild_id=0, bot=self.bot)
        description = (
            f"**{t('audit_log', 'field_id')}:** `{sound.id}`\n"
            f"**{t('audit_log', 'field_sound_name')}:** `{sound.name}`\n"
            f"**{t('audit_log', 'field_sound_emoji')}:** {sound.emoji if sound.emoji else f'`{t(\"audit_log\", \"none\")}`'}\n"
            f"**{t('audit_log', 'field_sound_volume')}:** `{int(sound.volume * 100)}%`\n"
            f"**{t('audit_log', 'field_sound_available')}:** `{t('audit_log', 'yes') if getattr(sound, 'available', True) else t('audit_log', 'no')}`"
        )
        if getattr(sound, 'user', None):
            description += f"\n**{t('audit_log', 'created_by')}:** {sound.user.mention} (`{sound.user.id}`)"
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.SUCCESS} {t('audit_log', 'sound_create_title')}",
            description=description,
            thumbnail_url=sound.user.display_avatar.url if getattr(sound, 'user', None) else None,
            guild=guild,
        )

    async def log_sound_delete(self, channel: discord.TextChannel, sound):
        guild = getattr(sound, 'guild', None)
        t = _(guild_id=guild.id, bot=self.bot) if guild else _(guild_id=0, bot=self.bot)
        description = (
            f"**{t('audit_log', 'field_id')}:** `{sound.id}`\n**{t('audit_log', 'field_sound_name')}:** `{sound.name}`\n"
            f"**{t('audit_log', 'field_sound_emoji')}:** {sound.emoji if sound.emoji else f'`{t(\"audit_log\", \"none\")}`'}"
        )
        if getattr(sound, 'user', None):
            description += f"\n**{t('audit_log', 'created_by')}:** {sound.user.mention} (`{sound.user.id}`)"
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.ERROR} {t('audit_log', 'sound_delete_title')}",
            description=description,
            thumbnail_url=sound.user.display_avatar.url if getattr(sound, 'user', None) else None,
            guild=guild,
        )

    async def log_sound_update(self, channel: discord.TextChannel, before, after):
        guild = getattr(after, 'guild', None)
        t = _(guild_id=guild.id, bot=self.bot) if guild else _(guild_id=0, bot=self.bot)
        fields = []
        if before.name != after.name:
            fields.append({"name": t('audit_log', 'field_sound_name'), "value": f"`{before.name}` ➜ `{after.name}`", "inline": False})
        if before.volume != after.volume:
            fields.append({"name": t('audit_log', 'field_sound_volume'), "value": f"`{int(before.volume * 100)}%` ➜ `{int(after.volume * 100)}%`", "inline": False})
        if before.emoji != after.emoji:
            fields.append({"name": t('audit_log', 'field_sound_emoji'), "value": f"{before.emoji or f'`{t(\"audit_log\", \"none\")}`'} ➜ {after.emoji or f'`{t(\"audit_log\", \"none\")}`'}", "inline": False})
        if getattr(before, 'available', True) != getattr(after, 'available', True):
            fields.append({"name": t('audit_log', 'field_sound_available'), "value": f"`{t('audit_log', 'yes') if getattr(before, 'available', True) else t('audit_log', 'no')}` ➜ `{t('audit_log', 'yes') if getattr(after, 'available', True) else t('audit_log', 'no')}`", "inline": False})
        if not fields:
            return
        description = f"**{t('audit_log', 'field_id')}:** `{after.id}`\n**{t('audit_log', 'field_sound_name')}:** `{after.name}`"
        if getattr(after, 'user', None):
            description += f"\n**{t('audit_log', 'created_by')}:** {after.user.mention} (`{after.user.id}`)"
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.UNKNOWN} {t('audit_log', 'sound_update_title')}",
            description=description, fields=fields,
            thumbnail_url=after.user.display_avatar.url if getattr(after, 'user', None) else None,
            guild=guild,
        )
