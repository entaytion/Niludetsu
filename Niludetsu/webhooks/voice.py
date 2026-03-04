import discord
from Niludetsu import Emojis
from Niludetsu.development.Webhooks import Webhooks

class VoiceLogger:
    """
    Логгер для действий в голосовых каналах через вебхук (максимум информации).
    """
    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.webhooks = Webhooks(bot)

    async def log_voice_join(self, log_channel: discord.TextChannel, member: discord.Member, channel: discord.VoiceChannel):
        description = f"**Пользователь:** {member.mention} (`{member.id}`)\n"
        description += f"**Канал:** {channel.mention} (`{channel.id}`)\n"
        description += f"**Категория:** `{channel.category.name if channel.category else 'Нет'}`\n"
        description += f"**Участников в канале:** `{len(channel.members)}/{channel.user_limit if channel.user_limit else '∞'}`"
        await self.webhooks.send_log(
            channel=log_channel,
            title=f"{Emojis.SUCCESS} Голосовой канал: пользователь присоединился",
            description=description,
            thumbnail_url=member.display_avatar.url,
            guild=member.guild
        )

    async def log_voice_leave(self, log_channel: discord.TextChannel, member: discord.Member, channel: discord.VoiceChannel):
        description = f"**Пользователь:** {member.mention} (`{member.id}`)\n"
        description += f"**Канал:** {channel.mention} (`{channel.id}`)\n"
        description += f"**Категория:** `{channel.category.name if channel.category else 'Нет'}`\n"
        description += f"**Участников в канале:** `{len(channel.members)}/{channel.user_limit if channel.user_limit else '∞'}`"
        await self.webhooks.send_log(
            channel=log_channel,
            title=f"{Emojis.ERROR} Голосовой канал: пользователь покинул",
            description=description,
            thumbnail_url=member.display_avatar.url,
            guild=member.guild
        )

    async def log_voice_switch(self, log_channel: discord.TextChannel, member: discord.Member, before: discord.VoiceChannel, after: discord.VoiceChannel):
        description = f"**Пользователь:** {member.mention} (`{member.id}`)\n"
        description += f"**Канал:** {before.mention if before else '`Нет`'} ➜ {after.mention if after else '`Нет`'}\n"
        description += f"**Категория:** `{before.category.name if before and before.category else 'Нет'}` ➜ `{after.category.name if after and after.category else 'Нет'}`\n"
        fields = []
        if before and after:
            fields.append({
                "name": "> Изменения:",
                "value": f"**Участников в старом канале:** `{len(before.members)}/{before.user_limit if before.user_limit else '∞'}`\n**Участников в новом канале:** `{len(after.members)}/{after.user_limit if after.user_limit else '∞'}`",
                "inline": False
            })
        await self.webhooks.send_log(
            channel=log_channel,
            title=f"{Emojis.UNKNOWN} Голосовой канал: пользователь перешел",
            description=description,
            fields=fields,
            thumbnail_url=member.display_avatar.url,
            guild=member.guild
        )
    # не уверен, что этот логгер нужен, но пусть будет. логгировать каждый пук я тоже ебал, если честно.
    async def log_voice_state(self, log_channel: discord.TextChannel, member: discord.Member, changes: dict):
        description = f"**Пользователь:** {member.mention} (`{member.id}`)\n"
        fields = []
        for change_type, (before, after) in changes.items():
            if change_type == 'deaf':
                fields.append({
                    "name": "> Изменения:",
                    "value": f"**Звук:** `{'Да' if before else 'Нет'}` ➜ `{'Да' if after else 'Нет'}`",
                    "inline": False
                })
            elif change_type == 'mute':
                fields.append({
                    "name": "> Изменения:",
                    "value": f"**Микрофон:** `{'Да' if before else 'Нет'}` ➜ `{'Да' if after else 'Нет'}`",
                    "inline": False
                })
            elif change_type == 'self_deaf':
                fields.append({
                    "name": "> Изменения:",
                    "value": f"**Звук (самостоятельно):** `{'Да' if before else 'Нет'}` ➜ `{'Да' if after else 'Нет'}`",
                    "inline": False
                })
            elif change_type == 'self_mute':
                fields.append({
                    "name": "> Изменения:",
                    "value": f"**Микрофон (самостоятельно):** `{'Да' if before else 'Нет'}` ➜ `{'Да' if after else 'Нет'}`",
                    "inline": False
                })
            elif change_type == 'self_stream':
                fields.append({
                    "name": "> Изменения:",
                    "value": f"**Стрим:** `{'Да' if before else 'Нет'}` ➜ `{'Да' if after else 'Нет'}`",
                    "inline": False
                })
            elif change_type == 'self_video':
                fields.append({
                    "name": "> Изменения:",
                    "value": f"**Видео:** `{'Да' if before else 'Нет'}` ➜ `{'Да' if after else 'Нет'}`",
                    "inline": False
                })
        if not fields:
            return
        await self.webhooks.send_log(
            channel=log_channel,
            title=f"{Emojis.UNKNOWN} Голосовой канал: обновлен",
            description=description,
            fields=fields,
            thumbnail_url=member.display_avatar.url,
            guild=member.guild
        ) 

