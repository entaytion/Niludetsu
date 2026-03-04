import discord
from Niludetsu import Emojis
from Niludetsu.development.Webhooks import Webhooks

PERMISSION_NAMES = {
    "add_reactions": "Добавлять реакции",
    "administrator": "Администратор",
    "attach_files": "Прикреплять файлы",
    "ban_members": "Банить участников",
    "change_nickname": "Изменять никнейм",
    "connect": "Подключаться",
    "create_instant_invite": "Создавать приглашения",
    "create_private_threads": "Создавать приватные ветки",
    "create_public_threads": "Создавать публичные ветки",
    "deafen_members": "Отключать звук участникам",
    "embed_links": "Встраивать ссылки",
    "external_emojis": "Использовать внешние эмодзи",
    "external_stickers": "Использовать внешние стикеры",
    "kick_members": "Выгонять участников",
    "manage_channels": "Управлять каналами",
    "manage_emojis": "Управлять эмодзи",
    "manage_emojis_and_stickers": "Управлять эмодзи и стикерами",
    "manage_events": "Управлять событиями",
    "manage_guild": "Управлять сервером",
    "manage_messages": "Управлять сообщениями",
    "manage_nicknames": "Управлять никнеймами",
    "manage_permissions": "Управлять правами",
    "manage_roles": "Управлять ролями",
    "manage_threads": "Управлять ветками",
    "manage_webhooks": "Управлять вебхуками",
    "mention_everyone": "Упоминать @everyone",
    "moderate_members": "Модерировать участников",
    "move_members": "Перемещать участников",
    "mute_members": "Отключать микрофон участникам",
    "priority_speaker": "Приоритетный голос",
    "read_message_history": "Читать историю сообщений",
    "read_messages": "Читать сообщения",
    "request_to_speak": "Запрашивать возможность говорить",
    "send_messages": "Отправлять сообщения",
    "send_messages_in_threads": "Отправлять сообщения в ветках",
    "send_tts_messages": "Отправлять TTS сообщения",
    "speak": "Говорить",
    "stream": "Стримить",
    "use_application_commands": "Использовать команды приложений",
    "use_embedded_activities": "Использовать встроенные активности",
    "use_external_emojis": "Использовать внешние эмодзи",
    "use_external_stickers": "Использовать внешние стикеры",
    "use_voice_activation": "Использовать активацию по голосу",
    "view_audit_log": "Просматривать журнал аудита",
    "view_channel": "Видеть каналы",
    "view_guild_insights": "Просматривать аналитику сервера",
}

class ChannelLogger:
    """
    Логгер для событий каналов через вебхук (максимум информации).
    """
    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.webhooks = Webhooks(bot)

    async def log_channel_create(self, log_channel: discord.TextChannel, channel: discord.abc.GuildChannel, creator: discord.User = None):
        title = f"{Emojis.SUCCESS} Канал: создан"
        description = f"**ID:** `{channel.id}`\n**Название:** `{channel.name}`\n**Тип:** `{str(channel.type)}`"
        if channel.category:
            description += f"\n**Категория:** `{channel.category.name}`"
        if creator:
            description += f"\n**Создатель:** {creator.mention} ({creator.id})"
        await self.webhooks.send_log(
            channel=log_channel,
            title=title,
            description=description,
            fields=[],
            thumbnail_url=None,
            guild=channel.guild
        )

    async def log_channel_delete(self, log_channel: discord.TextChannel, channel: discord.abc.GuildChannel, remover: discord.User = None):
        title = f"{Emojis.ERROR} Канал: удалён"
        description = f"**ID:** `{channel.id}`\n**Название:** `{channel.name}`\n**Тип:** `{str(channel.type)}`"
        if channel.category:
            description += f"\n**Категория:** `{channel.category.name}`"
        if remover:
            description += f"\n**Удалил:** {remover.mention} ({remover.id})"
        await self.webhooks.send_log(
            channel=log_channel,
            title=title,
            description=description,
            fields=[],
            thumbnail_url=None,
            guild=channel.guild
        )

    async def log_channel_update(self, log_channel: discord.TextChannel, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel, updater: discord.User = None, changes: list = None):
        title = f"{Emojis.UNKNOWN} Канал: изменён"
        description = f"**ID:** `{after.id}`\n**Название:** `{after.name}`\n**Тип:** `{str(after.type)}`"
        if after.category:
            description += f"\n**Категория:** `{after.category.name}`"
        if updater:
            description += f"\n**Обновил:** {updater.mention} ({updater.id})"
        fields = []
        if changes:
            for change in changes:
                fields.append({"name": "Изменение", "value": change, "inline": False})
        await self.webhooks.send_log(
            channel=log_channel,
            title=title,
            description=description,
            fields=fields,
            thumbnail_url=None,
            guild=after.guild
        )

    async def log_permissions_update(self, log_channel: discord.TextChannel, channel: discord.TextChannel, moderator: discord.Member, changes: list):
        title = f"{Emojis.UNKNOWN} Изменены права доступа в канале"
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
            channel=log_channel,
            title=title,
            description=description,
            fields=fields,
            guild=channel.guild
        )

class PinsLogger:
    """
    Логгер для изменений закрепленных сообщений (pins) через вебхук.
    """
    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.webhooks = Webhooks(bot)

    async def log_pins_update(self, channel: discord.TextChannel, last_pin: discord.Message = None):
        title = f"{Emojis.UNKNOWN} Пины: обновлены"
        description = f"**Канал:** {channel.mention} ({channel.id})"
        fields = []
        if last_pin:
            fields.append({"name": "Последний пин", "value": f"[Перейти к сообщению]({last_pin.jump_url})\nАвтор: {last_pin.author.mention} ({last_pin.author.id})\nВремя: <t:{int(last_pin.created_at.timestamp())}:F>", "inline": False})
        await self.webhooks.send_log(
            channel=channel,
            title=title,
            description=description,
            fields=fields,
            thumbnail_url=None,
            guild=channel.guild
        ) 

