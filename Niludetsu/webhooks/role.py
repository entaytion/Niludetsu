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

def get_permission_name(perm):
    return PERMISSION_NAMES.get(perm, perm.replace('_', ' ').title())

def permissions_list(perms: discord.Permissions):
    return [get_permission_name(perm) for perm, value in perms if value]

def permissions_diff(before: discord.Permissions, after: discord.Permissions):
    added = []
    removed = []
    for perm, value in after:
        if value and not getattr(before, perm):
            added.append(get_permission_name(perm))
    for perm, value in before:
        if value and not getattr(after, perm):
            removed.append(get_permission_name(perm))
    return added, removed

class RoleLogger:
    """
    Логгер для событий ролей через вебхук (максимум информации).
    """
    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.webhooks = Webhooks(bot)

    async def log_role_create(self, channel: discord.TextChannel, role: discord.Role):
        title = f"{Emojis.SUCCESS} Роль: создана"
        description = f"**Название:** {role.mention}\n**ID:** `{role.id}`\n**Цвет:** `{str(role.color)}`\n"
        description += f"**Позиция:** `{role.position}`\n"
        description += f"**Отображается отдельно:** `{'Да' if role.hoist else 'Нет'}`\n"
        description += f"**Упоминаемая:** `{'Да' if role.mentionable else 'Нет'}`"
        if role.icon:
            description += f"\n**Иконка:** `Есть`"
        perms = permissions_list(role.permissions)
        fields = []
        if perms:
            fields.append({"name": "Права", "value": ", ".join(f'`{p}`' for p in perms), "inline": False})
        await self.webhooks.send_log(
            channel=channel,
            title=title,
            description=description,
            fields=fields if fields else None,
            thumbnail_url=role.icon.url if role.icon else None,
            guild=role.guild
        )

    async def log_role_delete(self, channel: discord.TextChannel, role: discord.Role):
        title = f"{Emojis.ERROR} Роль: удалена"
        description = f"**Название:** `{role.name}`\n**ID:** `{role.id}`\n**Цвет:** `{str(role.color)}`"
        await self.webhooks.send_log(
            channel=channel,
            title=title,
            description=description,
            thumbnail_url=role.icon.url if role.icon else None,
            guild=role.guild
        )

    async def log_role_update(self, channel: discord.TextChannel, before: discord.Role, after: discord.Role):
        title = f"{Emojis.UNKNOWN} Роль: изменена"
        description = f"**Роль:** {after.mention}\n**ID:** `{after.id}`"
        fields = []
        if before.name != after.name:
            fields.append({"name": "Название", "value": f"`{before.name}` ➜ `{after.name}`", "inline": False})
        if before.color != after.color:
            fields.append({"name": "Цвет", "value": f"`{str(before.color)}` ➜ `{str(after.color)}`", "inline": False})
        if before.hoist != after.hoist:
            fields.append({"name": "Отображается отдельно", "value": f"`{'Да' if before.hoist else 'Нет'}` ➜ `{'Да' if after.hoist else 'Нет'}`", "inline": False})
        if before.mentionable != after.mentionable:
            fields.append({"name": "Упоминаемая", "value": f"`{'Да' if before.mentionable else 'Нет'}` ➜ `{'Да' if after.mentionable else 'Нет'}`", "inline": False})
        if before.icon != after.icon:
            fields.append({"name": "Иконка", "value": f"`{'Есть' if before.icon else 'Нет'}` ➜ `{'Есть' if after.icon else 'Нет'}`", "inline": False})
        # Права
        if before.permissions != after.permissions:
            added, removed = permissions_diff(before.permissions, after.permissions)
            if added:
                fields.append({"name": "Добавлены права", "value": ", ".join(f'`{p}`' for p in added), "inline": False})
            if removed:
                fields.append({"name": "Удалены права", "value": ", ".join(f'`{p}`' for p in removed), "inline": False})
        if not fields:
            return
        await self.webhooks.send_log(
            channel=channel,
            title=title,
            description=description,
            fields=fields,
            thumbnail_url=after.icon.url if after.icon else None,
            guild=after.guild
        ) 

