import discord
from Niludetsu import Emojis
from Niludetsu.development.Webhooks import Webhooks

class StageLogger:
    """
    Логгер для действий с трибунами (Stage) через вебхук (максимум информации).
    """
    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.webhooks = Webhooks(bot)

    async def log_stage_create(self, channel: discord.TextChannel, stage_instance: discord.StageInstance):
        title = f"{Emojis.SUCCESS} Трибуна: создана"
        description = f"**ID:** `{stage_instance.id}`\n"
        description += f"**Канал:** {stage_instance.channel.mention} (`{stage_instance.channel.id}`)\n"
        description += f"**Тема:** `{stage_instance.topic}`\n"
        description += f"**Приватность:** `{stage_instance.privacy_level.name}`\n"
        description += f"**Обнаружение отключено:** `{'Да' if stage_instance.discoverable_disabled else 'Нет'}`"
        fields = []
        if stage_instance.scheduled_event:
            fields.append({
                "name": "> Запланированное событие:",
                "value": f"`{stage_instance.scheduled_event.name}`",
                "inline": False
            })
        await self.webhooks.send_log(
            channel=channel,
            title=title,
            description=description,
            fields=fields,
            guild=stage_instance.guild
        )

    async def log_stage_delete(self, channel: discord.TextChannel, stage_instance: discord.StageInstance):
        title = f"{Emojis.ERROR} Трибуна: удалена"
        description = f"**ID:** `{stage_instance.id}`\n"
        description += f"**Канал:** {stage_instance.channel.mention} (`{stage_instance.channel.id}`)\n"
        description += f"**Тема:** `{stage_instance.topic}`"
        await self.webhooks.send_log(
            channel=channel,
            title=title,
            description=description,
            guild=stage_instance.guild
        )

    async def log_stage_update(self, channel: discord.TextChannel, before: discord.StageInstance, after: discord.StageInstance):
        title = f"{Emojis.UNKNOWN} Трибуна: обновлена"
        description = f"**ID:** `{after.id}`\n**Канал:** {after.channel.mention} (`{after.channel.id}`)"
        fields = []
        if before.topic != after.topic:
            fields.append({
                "name": "> Изменения:",
                "value": f"- Тема: `{before.topic}` ➜ `{after.topic}`",
                "inline": False
            })
        if before.privacy_level != after.privacy_level:
            fields.append({
                "name": "> Изменения:",
                "value": f"- Приватность: `{before.privacy_level.name}` ➜ `{after.privacy_level.name}`",
                "inline": False
            })
        if before.discoverable_disabled != after.discoverable_disabled:
            fields.append({
                "name": "> Изменения:",
                "value": f"- Обнаружение отключено: `{'Да' if before.discoverable_disabled else 'Нет'}` ➜ `{'Да' if after.discoverable_disabled else 'Нет'}`",
                "inline": False
            })
        if not fields:
            return
        await self.webhooks.send_log(
            channel=channel,
            title=title,
            description=description,
            fields=fields,
            guild=after.guild
        )

    async def log_stage_speaker_add(self, channel: discord.TextChannel, stage_instance: discord.StageInstance, member: discord.Member):
        title = f"{Emojis.SUCCESS} Трибуна: добавлен спикер"
        description = f"**Спикер:** {member.mention} (`{member.id}`)\n"
        description += f"**Канал:** {stage_instance.channel.mention} (`{stage_instance.channel.id}`)\n"
        description += f"**Тема:** `{stage_instance.topic}`"
        await self.webhooks.send_log(
            channel=channel,
            title=title,
            description=description,
            thumbnail_url=member.display_avatar.url,
            guild=stage_instance.guild
        )

    async def log_stage_speaker_remove(self, channel: discord.TextChannel, stage_instance: discord.StageInstance, member: discord.Member):
        title = f"{Emojis.ERROR} Трибуна: удален спикер"
        description = f"**Спикер:** {member.mention} (`{member.id}`)\n"
        description += f"**Канал:** {stage_instance.channel.mention} (`{stage_instance.channel.id}`)\n"
        description += f"**Тема:** `{stage_instance.topic}`"
        await self.webhooks.send_log(
            channel=channel,
            title=title,
            description=description,
            thumbnail_url=member.display_avatar.url,
            guild=stage_instance.guild
        )

    async def log_stage_request_speak(self, channel: discord.TextChannel, stage_instance: discord.StageInstance, member: discord.Member):
        title = f"{Emojis.UNKNOWN} Трибуна: запрос на выступление"
        description = f"**Пользователь:** {member.mention} (`{member.id}`)\n"
        description += f"**Канал:** {stage_instance.channel.mention} (`{stage_instance.channel.id}`)\n"
        description += f"**Тема:** `{stage_instance.topic}`"
        await self.webhooks.send_log(
            channel=channel,
            title=title,
            description=description,
            thumbnail_url=member.display_avatar.url,
            guild=stage_instance.guild
        ) 

