import discord
from Niludetsu import Emojis
from Niludetsu.development.Webhooks import Webhooks

class SoundboardLogger:
    """
    Логгер для действий со звуками Soundboard через вебхук (максимум информации).
    """
    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.webhooks = Webhooks(bot)

    async def log_sound_create(self, channel: discord.TextChannel, sound):
        title = f"{Emojis.SUCCESS} Звук: добавлен"
        description = f"**ID:** `{sound.id}`\n"
        description += f"**Название:** `{sound.name}`\n"
        description += f"**Эмодзи:** {sound.emoji if sound.emoji else '`Нет`'}\n"
        description += f"**Громкость:** `{int(sound.volume * 100)}%`\n"
        description += f"**Доступен:** `{'Да' if getattr(sound, 'available', True) else 'Нет'}`"
        if getattr(sound, 'user', None):
            description += f"\n**Создатель:** {sound.user.mention} (`{sound.user.id}`)"
        await self.webhooks.send_log(
            channel=channel,
            title=title,
            description=description,
            thumbnail_url=sound.user.display_avatar.url if getattr(sound, 'user', None) else None,
            guild=sound.guild if getattr(sound, 'guild', None) else None
        )

    async def log_sound_delete(self, channel: discord.TextChannel, sound):
        title = f"{Emojis.ERROR} Звук: удален"
        description = f"**ID:** `{sound.id}`\n"
        description += f"**Название:** `{sound.name}`\n"
        description += f"**Эмодзи:** {sound.emoji if sound.emoji else '`Нет`'}"
        if getattr(sound, 'user', None):
            description += f"\n**Создатель:** {sound.user.mention} (`{sound.user.id}`)"
        await self.webhooks.send_log(
            channel=channel,
            title=title,
            description=description,
            thumbnail_url=sound.user.display_avatar.url if getattr(sound, 'user', None) else None,
            guild=sound.guild if getattr(sound, 'guild', None) else None
        )

    async def log_sound_update(self, channel: discord.TextChannel, before, after):
        title = f"{Emojis.UNKNOWN} Звук: обновлен"
        description = f"**ID:** `{after.id}`\n**Название:** `{after.name}`"
        fields = []
        if before.name != after.name:
            fields.append({
                "name": "> Изменения:",
                "value": f"- Название: `{before.name}` ➜ `{after.name}`",
                "inline": False
            })
        if before.volume != after.volume:
            fields.append({
                "name": "> Изменения:",
                "value": f"- Громкость: `{int(before.volume * 100)}%` ➜ `{int(after.volume * 100)}%`",
                "inline": False
            })
        if before.emoji != after.emoji:
            fields.append({
                "name": "> Изменения:",
                "value": f"- Эмодзи: {before.emoji if before.emoji else '`Нет`'} ➜ {after.emoji if after.emoji else '`Нет`'}",
                "inline": False
            })
        if getattr(before, 'available', True) != getattr(after, 'available', True):
            fields.append({
                "name": "> Изменения:",
                "value": f"- Доступен: `{'Да' if getattr(before, 'available', True) else 'Нет'}` ➜ `{'Да' if getattr(after, 'available', True) else 'Нет'}`",
                "inline": False
            })
        if not fields:
            return
        if getattr(after, 'user', None):
            description += f"\n**Создатель:** {after.user.mention} (`{after.user.id}`)"
        await self.webhooks.send_log(
            channel=channel,
            title=title,
            description=description,
            fields=fields,
            thumbnail_url=after.user.display_avatar.url if getattr(after, 'user', None) else None,
            guild=after.guild if getattr(after, 'guild', None) else None
        )
    # эта хуйня вообще работает? я сколько не тыкал оно не работает, xd. даже если в discord.py это введут, я удалю нахуй его.
    async def log_sound_play(self, channel: discord.TextChannel, sound, member: discord.Member):
        title = f"{Emojis.SUCCESS} Звук: воспроизведён"
        description = f"**Пользователь:** {member.mention} (`{member.id}`)\n"
        description += f"**Звук:** `{sound.name}` (`{sound.id}`)\n"
        description += f"**Эмодзи:** {sound.emoji if sound.emoji else '`Нет`'}\n"
        description += f"**Громкость:** `{int(sound.volume * 100)}%`"
        await self.webhooks.send_log(
            channel=channel,
            title=title,
            description=description,
            thumbnail_url=member.display_avatar.url,
            guild=sound.guild if getattr(sound, 'guild', None) else None
        ) 

