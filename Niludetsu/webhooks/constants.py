"""
Общие константы для системы логирования.
Все названия прав доступа — на русском.
"""

# Полный маппинг discord.Permissions → русские названия
PERMISSION_NAMES = {
    # ——— Общие ———
    "administrator": "Администратор",
    "view_audit_log": "Просмотр журнала аудита",
    "view_guild_insights": "Просмотр аналитики сервера",
    "manage_guild": "Управление сервером",
    "manage_roles": "Управление ролями",
    "manage_permissions": "Управление правами",
    "manage_channels": "Управление каналами",
    "manage_webhooks": "Управление вебхуками",
    "manage_expressions": "Управление выражениями",
    "manage_emojis": "Управление эмодзи",
    "manage_emojis_and_stickers": "Управление эмодзи и стикерами",
    "manage_events": "Управление событиями",
    "manage_threads": "Управление ветками",
    "manage_nicknames": "Управление никнеймами",
    "manage_messages": "Управление сообщениями",
    # ——— Участники ———
    "create_instant_invite": "Создание приглашений",
    "kick_members": "Выгонять участников",
    "ban_members": "Банить участников",
    "moderate_members": "Модерировать участников (тайм-аут)",
    "change_nickname": "Изменять никнейм",
    "move_members": "Перемещать участников",
    "mute_members": "Отключать микрофон участникам",
    "deafen_members": "Отключать звук участникам",
    # ——— Текстовые каналы ———
    "view_channel": "Просмотр каналов",
    "read_messages": "Чтение сообщений",
    "read_message_history": "Чтение истории сообщений",
    "send_messages": "Отправка сообщений",
    "send_messages_in_threads": "Отправка сообщений в ветках",
    "send_tts_messages": "Отправка TTS сообщений",
    "send_voice_messages": "Отправка голосовых сообщений",
    "embed_links": "Встраивание ссылок",
    "attach_files": "Прикрепление файлов",
    "add_reactions": "Добавление реакций",
    "mention_everyone": "Упоминание @everyone",
    "use_application_commands": "Использование команд приложений",
    "use_external_emojis": "Внешние эмодзи",
    "use_external_stickers": "Внешние стикеры",
    "external_emojis": "Внешние эмодзи",
    "external_stickers": "Внешние стикеры",
    # ——— Ветки ———
    "create_public_threads": "Создание публичных веток",
    "create_private_threads": "Создание приватных веток",
    # ——— Голосовые каналы ———
    "connect": "Подключение",
    "speak": "Говорить",
    "stream": "Стрим (Go Live)",
    "use_voice_activation": "Активация по голосу",
    "priority_speaker": "Приоритетный голос",
    "request_to_speak": "Запрос на выступление",
    "use_soundboard": "Использование звуковой панели",
    "use_external_sounds": "Внешние звуки",
    # ——— Активности ———
    "use_embedded_activities": "Встроенные активности",
    "create_events": "Создание событий",
    "create_polls": "Создание опросов",
    # ——— Монетизация ———
    "create_expressions": "Создание выражений",
    "view_creator_monetization_analytics": "Просмотр аналитики монетизации",
}


def get_permission_name(perm: str) -> str:
    """Получить русское название права доступа."""
    return PERMISSION_NAMES.get(perm, perm.replace('_', ' ').title())


def permissions_list(perms) -> list[str]:
    """Получить список включенных прав."""
    return [get_permission_name(perm) for perm, value in perms if value]


def permissions_diff(before, after) -> tuple[list[str], list[str]]:
    """Сравнить два набора прав, вернуть (добавленные, удалённые)."""
    added = []
    removed = []
    for perm, value in after:
        if value and not getattr(before, perm):
            added.append(get_permission_name(perm))
    for perm, value in before:
        if value and not getattr(after, perm):
            removed.append(get_permission_name(perm))
    return added, removed
