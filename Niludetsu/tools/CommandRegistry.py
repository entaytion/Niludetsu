"""Общий реестр команд и категорий для справки и контроля доступа."""

from copy import deepcopy
from Niludetsu import Emojis
from typing import Dict, List

class CommandType:
    HYBRID = "hybrid"
    PREFIX = "prefix"
    SLASH = "slash"

_BASE_REGISTRY: Dict[str, Dict[str, object]] = {
    "economy": {
        "title": "Экономика",
        "emoji": Emojis.hECONOMY,
        "command_list": [
            {"name": "balance", "aliases": ["b"], "description": "Показать информацию о балансе", "required_args": [], "optional_args": ["юзер"], "type": CommandType.HYBRID},
            {"name": "blackjack", "aliases": ["bj"], "description": "Сыграть в блекджек", "required_args": ["ставка"], "optional_args": [], "type": CommandType.HYBRID},
            {"name": "casino", "aliases": ["roulette"], "description": "Сыграть в рулетку", "required_args": ["ставка"], "optional_args": ["число"], "type": CommandType.HYBRID},
            {"name": "coinflip", "aliases": ["монетка"], "description": "Подбросить монетку", "required_args": ["ставка"], "optional_args": [], "type": CommandType.HYBRID},
            {"name": "daily", "aliases": ["timely"], "description": "Получить ежедневную награду", "required_args": [], "optional_args": [], "type": CommandType.HYBRID},
            {"name": "deposit", "aliases": ["dep"], "description": "Внести деньги на банковский счёт", "required_args": ["сумма"], "optional_args": [], "type": CommandType.HYBRID},
            {"name": "duel", "aliases": [], "description": "Вызвать игрока на дуэль", "required_args": ["игрок", "ставка"], "optional_args": [], "type": CommandType.HYBRID},
            {"name": "income", "aliases": [], "description": "Получить доход с ролей", "required_args": [], "optional_args": [], "type": CommandType.HYBRID},
            {"name": "pay", "aliases": [], "description": "Перевести деньги другому пользователю", "required_args": ["игрок", "сумма"], "optional_args": [], "type": CommandType.HYBRID},
            {"name": "rob", "aliases": [], "description": "Попытаться ограбить пользователя", "required_args": ["игрок"], "optional_args": [], "type": CommandType.HYBRID},
            {"name": "shop", "aliases": [], "description": "Открыть магазин ролей", "required_args": [], "optional_args": [], "type": CommandType.HYBRID},
            {"name": "slut", "aliases": [], "description": "Рискованный способ заработка", "required_args": [], "optional_args": [], "type": CommandType.HYBRID},
            {"name": "slots", "aliases": [], "description": "Сыграть в слоты", "required_args": ["ставка"], "optional_args": [], "type": CommandType.HYBRID},
            {"name": "withdraw", "aliases": ["wd"], "description": "Вывести деньги с банковского счёта", "required_args": [], "optional_args": ["сумма"], "type": CommandType.HYBRID},
            {"name": "withdrawfamily", "aliases": [], "description": "Снять деньги с семейного счета", "required_args": [], "optional_args": ["сумма"], "type": CommandType.HYBRID},
            {"name": "work", "aliases": [], "description": "Заработать кривены", "required_args": [], "optional_args": [], "type": CommandType.HYBRID},
            {"name": "transactions", "aliases": ["tx", "транзакции"], "description": "История транзакций", "required_args": [], "optional_args": ["юзер"], "type": CommandType.HYBRID},
        ],
    },
    "fun": {
        "title": "Развлечения",
        "emoji": Emojis.hFUN,
        "command_list": [
            {"name": "8ball", "aliases": [], "description": "Задать вопрос магическому шару", "required_args": ["вопрос"], "optional_args": [], "type": CommandType.HYBRID},
            {"name": "nsfw", "aliases": ["rnsfw", "realnsfw"], "description": "Сам играйся со своим причандалом", "required_args": [], "optional_args": [], "type": CommandType.HYBRID},
            {"name": "rps", "aliases": ["кнб"], "description": "Камень-Ножницы-Бумага", "required_args": ["user"], "optional_args": ["ставка"], "type": CommandType.HYBRID},
        ],
    },
    "main": {
        "title": "Основные",
        "emoji": Emojis.hSETTINGS,
        "command_list": [
            {"name": "help", "aliases": [], "description": "Справочник по командам", "required_args": [], "optional_args": [], "type": CommandType.HYBRID},
            {"name": "about", "aliases": [], "description": "Информация о боте", "required_args": [], "optional_args": [], "type": CommandType.SLASH},
            {"name": "info", "aliases": ["инфо",], "description": "Информация о том, что вы введёте в аргументах.\n  - **К примеру:** ``!info role/роль id/упоминание``", "required_args": [], "optional_args": ["server", "bot", "user", "emoji", "channel", "invite"], "type": CommandType.PREFIX},
            {"name": "server", "aliases": ["serverinfo", "сервер"], "description": "Информация о сервере", "required_args": [], "optional_args": [], "type": CommandType.HYBRID},
            {"name": "roleinfo", "aliases": [], "description": "Информация о пользователе", "required_args": ["role"], "optional_args": [], "type": CommandType.SLASH},
            {"name": "userinfo", "aliases": [], "description": "Информация о пользователе", "required_args": [], "optional_args": ["user"], "type": CommandType.SLASH},
            {"name": "channelinfo", "aliases": [], "description": "Информация о канале", "required_args": [], "optional_args": ["channel"], "type": CommandType.SLASH},
        ],
    },
    "moderation": {
        "title": "Модерация",
        "emoji": Emojis.hMODERATION,
        "command_list": [
            {"name": "automod", "aliases": [], "description": "Настройка автомодерации", "required_args": [], "optional_args": [], "type": CommandType.PREFIX},
            {"name": "ban", "aliases": [], "description": "Заблокировать пользователя", "required_args": ["user"], "optional_args": ["reason", "days"], "type": CommandType.HYBRID},
            {"name": "clear", "aliases": [], "description": "Очистить сообщения", "required_args": ["amount"], "optional_args": ["user"], "type": CommandType.HYBRID},
            {"name": "lock", "aliases": [], "description": "Заблокировать канал", "required_args": ["channel"], "optional_args": ["reason"], "type": CommandType.HYBRID},
            {"name": "massrole", "aliases": [], "description": "Массовая выдача ролей", "required_args": ["role"], "optional_args": ["action"], "type": CommandType.HYBRID},
            {"name": "mute", "aliases": [], "description": "Заглушить пользователя", "required_args": ["user"], "optional_args": ["duration", "reason"], "type": CommandType.HYBRID},
            {"name": "rudiments", "aliases": [], "description": "Посмотреть список наказаний пользователя", "required_args": [], "optional_args": ["user"], "type": CommandType.HYBRID},
            {"name": "slowmode", "aliases": [], "description": "Установить медленный режим", "required_args": ["seconds"], "optional_args": ["channel"], "type": CommandType.HYBRID},
            {"name": "unban", "aliases": [], "description": "Разблокировать пользователя", "required_args": ["user"], "optional_args": ["reason"], "type": CommandType.HYBRID},
            {"name": "unlock", "aliases": [], "description": "Разблокировать канал", "required_args": ["channel"], "optional_args": ["reason"], "type": CommandType.HYBRID},
            {"name": "unmute", "aliases": [], "description": "Снять заглушку с пользователя", "required_args": ["user"], "optional_args": ["reason"], "type": CommandType.HYBRID},
            {"name": "unwarn", "aliases": [], "description": "Снять предупреждение с пользователя", "required_args": ["user", "warn_id"], "optional_args": ["reason"], "type": CommandType.HYBRID},
            {"name": "warn", "aliases": [], "description": "Выдать предупреждение пользователю", "required_args": ["user"], "optional_args": ["reason"], "type": CommandType.HYBRID},
        ],
    },
    "music": {
        "title": "Музыка",
        "emoji": Emojis.hMUSIC,
        "command_list": [
            {"name": "leave", "aliases": [], "description": "Отключить бота от голосового канала", "type": CommandType.SLASH},
            {"name": "nightcore", "aliases": [], "description": "Включить/выключить эффект nightcore", "type": CommandType.SLASH},
            {"name": "np", "aliases": [], "description": "Показать текущий трек", "type": CommandType.SLASH},
            {"name": "pause", "aliases": [], "description": "Поставить воспроизведение на паузу", "type": CommandType.SLASH},
            {"name": "play", "aliases": [], "description": "Проигрывать музыку", "type": CommandType.SLASH},
            {"name": "queue", "aliases": [], "description": "Показать очередь воспроизведения", "type": CommandType.SLASH},
            {"name": "repeat", "aliases": [], "description": "Включить/выключить повтор", "type": CommandType.SLASH},
            {"name": "resume", "aliases": [], "description": "Возобновить воспроизведение", "type": CommandType.SLASH},
            {"name": "shuffle", "aliases": [], "description": "Перемешать очередь воспроизведения", "type": CommandType.SLASH},
            {"name": "skip", "aliases": [], "description": "Пропустить текущий трек", "type": CommandType.SLASH},
            {"name": "volume", "aliases": [], "description": "Изменить громкость воспроизведения", "type": CommandType.SLASH},
        ],
    },
    "profile": {
        "title": "Профиль",
        "emoji": Emojis.hPROFILE,
        "command_list": [
            {"name": "achievements", "aliases": [], "description": "Показать достижения пользователя", "optional_args": ["user"], "type": CommandType.HYBRID},
            {"name": "avatar", "aliases": ["аватар"], "description": "Показать аватарку пользователя", "optional_args": ["lgbt"], "type": CommandType.HYBRID},
            {"name": "child", "aliases": ["усыновить", "удочерить", "ребенок"], "description": "Усыновить пользователя", "required_args": ["user"], "optional_args": [], "type": CommandType.HYBRID},
            {"name": "divorce", "aliases": ["развестись", "расторгнуть", "развод"], "description": "Развестись с текущим партнером", "required_args": [], "optional_args": [], "type": CommandType.HYBRID},
            {"name": "kidshouse", "aliases": ["детдом", "отказаться", "отпустить"], "description": "Отпустить усыновленного пользователя", "required_args": ["user"], "optional_args": [], "type": CommandType.HYBRID},
            {"name": "leaderboard", "aliases": [], "description": "Показать таблицу лидеров", "type": CommandType.HYBRID},
            {"name": "level", "aliases": [], "optional_args": ["user"], "description": "Показать уровень пользователя", "type": CommandType.HYBRID},
            {"name": "marry", "aliases": ["предложение", "женитьба", "свадьба", "жениться"], "description": "Сделать предложение пользователю", "required_args": ["user"], "optional_args": [], "type": CommandType.HYBRID},
            {"name": "relations", "aliases": ["брак", "отношения"], "description": "Показать сколько времени вы с партнером вместе", "required_args": [], "optional_args": ["user"], "type": CommandType.HYBRID},
            {"name": "profile", "aliases": [], "description": "Показать профиль пользователя", "type": CommandType.HYBRID},
        ],
    },
    "reactions": {
        "title": "Реакции",
        "emoji": Emojis.hREACTIONS,
        "command_list": [
            {"name": "anal", "aliases": ["анал"], "description": "Заняться анальным сексом (NSFW)", "required_args": ["user"], "type": CommandType.HYBRID},
            {"name": "bite", "aliases": ["укусить", "кусь", "кусать"], "description": "Укусить пользователя", "required_args": ["user"], "type": CommandType.HYBRID},
            {"name": "blowjob", "aliases": ["минет"], "description": "Сделать минет (NSFW)", "required_args": ["user"], "type": CommandType.HYBRID},
            {"name": "cry", "aliases": ["плакать", "реветь", "рыдать"], "description": "Расплакаться", "type": CommandType.HYBRID},
            {"name": "cum", "aliases": ["кончить"], "description": "Кончить на пользователя (NSFW)", "required_args": ["user"], "type": CommandType.HYBRID},
            {"name": "dance", "aliases": ["танцевать"], "description": "Танцевать", "type": CommandType.HYBRID},
            {"name": "fuck", "aliases": ["выебать", "трахнуть"], "description": "Выебать пользователя (NSFW)", "required_args": ["user"], "type": CommandType.HYBRID},
            {"name": "hug", "aliases": ["обнять", "обнимашки", "обнимать"], "description": "Обнять пользователя", "required_args": ["user"], "type": CommandType.HYBRID},
            {"name": "kiss", "aliases": ["поцеловать", "чмок", "поцелуй"], "description": "Поцеловать пользователя", "required_args": ["user"], "type": CommandType.HYBRID},
            {"name": "love", "aliases": [], "description": "Признаться в любви", "required_args": ["user"], "type": CommandType.HYBRID},
            {"name": "mad", "aliases": ["злиться"], "description": "Разозлиться", "type": CommandType.HYBRID},
            {"name": "nervous", "aliases": ["нервничать"], "description": "Нервничать", "type": CommandType.HYBRID},
            {"name": "pat", "aliases": ["погладить"], "description": "Погладить пользователя", "required_args": ["user"], "type": CommandType.HYBRID},
            {"name": "pussylick", "aliases": ["куни", "куннилингус"], "description": "Сделать куннилингус (NSFW)", "required_args": ["user"], "type": CommandType.HYBRID},
            {"name": "sex", "aliases": ["заняться", "секс"], "description": "Заняться любовью с пользователем (NSFW)", "required_args": ["user"], "type": CommandType.HYBRID},
            {"name": "slap", "aliases": ["ударить", "шлепнуть", "шлёпнуть"], "description": "Ударить пользователя", "required_args": ["user"], "type": CommandType.HYBRID},
            {"name": "sneeze", "aliases": ["чихнуть", "апчхи", "чих"], "description": "Чихнуть", "type": CommandType.HYBRID},
            {"name": "solo", "aliases": ["мастурбация", "мастурбировать"], "description": "Мастурбировать (NSFW)", "required_args": [], "type": CommandType.HYBRID},
            {"name": "sorry", "aliases": ["извиниться"], "description": "Извиниться перед пользователем", "required_args": ["user"], "type": CommandType.HYBRID},
            {"name": "tickle", "aliases": ["щекотать", "пощекотать", "щекотка"], "description": "Пощекотать пользователя", "required_args": ["user"], "type": CommandType.HYBRID},
        ],
    },
    "tools": {
        "title": "Утилиты",
        "emoji": Emojis.hTOOLS,
        "command_list": [
            {"name": "ascii", "aliases": [], "description": "Создать ASCII арт из текста", "required_args": ["текст"], "optional_args": ["шрифт"], "type": CommandType.PREFIX},
            {"name": "color", "aliases": [], "description": "Информация о цвете", "type": CommandType.PREFIX},
            {"name": "currency", "aliases": [], "description": "Конвертация валют", "type": CommandType.PREFIX},
            {"name": "exchange", "aliases": [], "description": "Курсы валют", "type": CommandType.PREFIX},
            {"name": "hash", "aliases": [], "description": "Получить хеш текста (MD5, SHA256)", "required_args": ["текст"], "optional_args": ["алгоритм"], "type": CommandType.PREFIX},
            {"name": "k", "aliases": [], "description": "Калькулятор", "type": CommandType.PREFIX},
            {"name": "math", "aliases": [], "description": "Решение математических задач", "type": CommandType.PREFIX},
            {"name": "ping", "aliases": [], "description": "Проверить пинг до сервера", "type": CommandType.PREFIX},
            {"name": "rand", "aliases": [], "description": "Случайное число", "type": CommandType.PREFIX},
            {"name": "reminder", "aliases": [], "description": "Установить напоминание", "type": CommandType.PREFIX},
            {"name": "screenshot", "aliases": ["скрин", "ss"], "description": "Создать скриншот веб-страницы", "required_args": ["url"], "optional_args": [], "type": CommandType.PREFIX},
            {"name": "t", "aliases": [], "description": "Перевод текста", "type": CommandType.PREFIX},
            {"name": "translate", "aliases": [], "description": "Перевод текста", "type": CommandType.PREFIX},
            {"name": "weather", "aliases": [], "description": "Узнать погоду", "type": CommandType.PREFIX},
            {"name": "whois", "aliases": [], "description": "Информация о домене/IP адресе", "type": CommandType.PREFIX},
            {"name": "afk", "aliases": ["афк"], "description": "Установить AFK-статус", "required_args": [], "optional_args": ["причина"], "type": CommandType.HYBRID},
        ],
    },
    "admin": {
        "title": "Администрирование",
        "emoji": Emojis.hADMIN,
        "command_list": [
            {"name": "analytics", "aliases": [], "description": "Аналитика сервера", "type": CommandType.HYBRID},
            {"name": "bump", "aliases": [], "description": "Получение текущего времени для bump-команды", "type": CommandType.PREFIX},
            {"name": "giveaway", "aliases": [], "description": "Создать розыгрыш", "type": CommandType.PREFIX},
            {"name": "partnership", "aliases": [], "description": "Статистика партнерства", "required_args": [], "optional_args": ["user_id"], "type": CommandType.PREFIX},
            {"name": "rewards", "aliases": [], "description": "Управление наградами сервера для партнёр-менеджеров", "type": CommandType.PREFIX},
        ],
    },
}

def get_command_registry() -> Dict[str, Dict[str, object]]:
    """Возвращает копию реестра команд с отсортированными списками."""
    registry = deepcopy(_BASE_REGISTRY)
    for data in registry.values():
        commands: List[Dict[str, object]] = data.get("command_list", [])  # type: ignore[assignment]
        commands.sort(key=lambda item: item.get("name", ""))
    return registry

__all__ = ["CommandType", "get_command_registry"]

