"""
Пул квестов: большой набор, из которого рандомно выбираются для каждого юзера.

Каждый квест:
    key:         уникальный ключ (str)
    name:        человекочитаемое название
    description: описание квеста
    type:        тип трекинга: "messages" | "voice_minutes" | "bump"
    goal:        числовая цель (int)
    reward:      награда в монетах (int)
    reset:       период сброса: "daily" | "weekly"
"""

from typing import Any, Dict, List

QuestDef = Dict[str, Any]

# Сколько квестов выбирается для юзера за период
DAILY_QUEST_COUNT = 3
WEEKLY_QUEST_COUNT = 3


# ——— ПУЛ ЕЖЕДНЕВНЫХ КВЕСТОВ ———
DAILY_POOL: List[QuestDef] = [
    # --- Сообщения ---
    {
        "key": "d_msg_25",
        "name": "Новичок чата",
        "description": "Напиши 25 сообщений за день.",
        "type": "messages",
        "goal": 25,
        "reward": 150,
        "reset": "daily",
    },
    {
        "key": "d_msg_50",
        "name": "Активный чаттер",
        "description": "Отправь 50 сообщений за день.",
        "type": "messages",
        "goal": 50,
        "reward": 300,
        "reset": "daily",
    },
    {
        "key": "d_msg_100",
        "name": "Болтун",
        "description": "Докажи, что умеешь говорить — 100 сообщений за день.",
        "type": "messages",
        "goal": 100,
        "reward": 500,
        "reset": "daily",
    },
    {
        "key": "d_msg_200",
        "name": "Графоман",
        "description": "Напиши целых 200 сообщений. Ты вообще спишь?",
        "type": "messages",
        "goal": 200,
        "reward": 800,
        "reset": "daily",
    },
    {
        "key": "d_msg_15",
        "name": "Доброе утро",
        "description": "Напиши хотя бы 15 сообщений сегодня.",
        "type": "messages",
        "goal": 15,
        "reward": 100,
        "reset": "daily",
    },
    {
        "key": "d_msg_75",
        "name": "Душа компании",
        "description": "Отправь 75 сообщений — покажи что ты тут главный.",
        "type": "messages",
        "goal": 75,
        "reward": 400,
        "reset": "daily",
    },
    # --- Войс ---
    {
        "key": "d_voice_15",
        "name": "Быстрый заход",
        "description": "Посиди 15 минут в голосовом канале.",
        "type": "voice_minutes",
        "goal": 15,
        "reward": 100,
        "reset": "daily",
    },
    {
        "key": "d_voice_30",
        "name": "Быстрый созвон",
        "description": "Проведи 30 минут в войсе.",
        "type": "voice_minutes",
        "goal": 30,
        "reward": 200,
        "reset": "daily",
    },
    {
        "key": "d_voice_60",
        "name": "Чайная церемония",
        "description": "Разогрей голосовые связки — 1 час в войсе.",
        "type": "voice_minutes",
        "goal": 60,
        "reward": 300,
        "reset": "daily",
    },
    {
        "key": "d_voice_120",
        "name": "Голосовой марафон",
        "description": "Просиди 2 часа в войсе. Уши не отвалятся.",
        "type": "voice_minutes",
        "goal": 120,
        "reward": 600,
        "reset": "daily",
    },
    {
        "key": "d_voice_45",
        "name": "На связи",
        "description": "Проведи 45 минут в голосовом канале.",
        "type": "voice_minutes",
        "goal": 45,
        "reward": 250,
        "reset": "daily",
    },
    # --- Бампы ---
    {
        "key": "d_bump_1",
        "name": "Напоминание",
        "description": "Напомни всем, что мы существуем — 1 бамп.",
        "type": "bump",
        "goal": 1,
        "reward": 200,
        "reset": "daily",
    },
    {
        "key": "d_bump_2",
        "name": "Двойной удар",
        "description": "Сделай 2 бампа за день.",
        "type": "bump",
        "goal": 2,
        "reward": 400,
        "reset": "daily",
    },
    {
        "key": "d_bump_3",
        "name": "Тройной бамп",
        "description": "Ударь по трём мониторингам за день.",
        "type": "bump",
        "goal": 3,
        "reward": 600,
        "reset": "daily",
    },
]

# ——— ПУЛ НЕДЕЛЬНЫХ КВЕСТОВ ———
WEEKLY_POOL: List[QuestDef] = [
    # --- Сообщения ---
    {
        "key": "w_msg_200",
        "name": "Разговорчивый",
        "description": "Напиши 200 сообщений за неделю.",
        "type": "messages",
        "goal": 200,
        "reward": 1000,
        "reset": "weekly",
    },
    {
        "key": "w_msg_500",
        "name": "Марафонец",
        "description": "Отправь 500 сообщений за неделю.",
        "type": "messages",
        "goal": 500,
        "reward": 2500,
        "reset": "weekly",
    },
    {
        "key": "w_msg_1000",
        "name": "Летописец",
        "description": "1000 сообщений за неделю. Легенда чата.",
        "type": "messages",
        "goal": 1000,
        "reward": 5000,
        "reset": "weekly",
    },
    {
        "key": "w_msg_350",
        "name": "Социальная бабочка",
        "description": "Напиши 350 сообщений за неделю.",
        "type": "messages",
        "goal": 350,
        "reward": 1800,
        "reset": "weekly",
    },
    {
        "key": "w_msg_750",
        "name": "Без замолку",
        "description": "750 сообщений за неделю — тебя не заткнуть.",
        "type": "messages",
        "goal": 750,
        "reward": 3500,
        "reset": "weekly",
    },
    # --- Войс ---
    {
        "key": "w_voice_120",
        "name": "Войс-энтузиаст",
        "description": "Проведи 2 часа в голосовых каналах за неделю.",
        "type": "voice_minutes",
        "goal": 120,
        "reward": 800,
        "reset": "weekly",
    },
    {
        "key": "w_voice_300",
        "name": "Диджей",
        "description": "Просиди 5 часов в голосовых каналах за неделю.",
        "type": "voice_minutes",
        "goal": 300,
        "reward": 1500,
        "reset": "weekly",
    },
    {
        "key": "w_voice_600",
        "name": "Вечный созвон",
        "description": "10 часов в войсе за неделю. Ты там живёшь?",
        "type": "voice_minutes",
        "goal": 600,
        "reward": 3000,
        "reset": "weekly",
    },
    {
        "key": "w_voice_180",
        "name": "Голосовой гуру",
        "description": "3 часа в войсе за неделю.",
        "type": "voice_minutes",
        "goal": 180,
        "reward": 1000,
        "reset": "weekly",
    },
    {
        "key": "w_voice_420",
        "name": "Звуковая стена",
        "description": "7 часов в войсе за неделю.",
        "type": "voice_minutes",
        "goal": 420,
        "reward": 2000,
        "reset": "weekly",
    },
    # --- Бампы ---
    {
        "key": "w_bump_3",
        "name": "Новичок промо",
        "description": "Сделай 3 бампа за неделю.",
        "type": "bump",
        "goal": 3,
        "reward": 600,
        "reset": "weekly",
    },
    {
        "key": "w_bump_5",
        "name": "Промоутер",
        "description": "Сделай 5 бампов за неделю.",
        "type": "bump",
        "goal": 5,
        "reward": 1000,
        "reset": "weekly",
    },
    {
        "key": "w_bump_10",
        "name": "Амбассадор",
        "description": "Целых 10 бампов за неделю. Ты — лицо сервера.",
        "type": "bump",
        "goal": 10,
        "reward": 2000,
        "reset": "weekly",
    },
    {
        "key": "w_bump_7",
        "name": "Каждый день на посту",
        "description": "Сделай 7 бампов за неделю — по одному в день!",
        "type": "bump",
        "goal": 7,
        "reward": 1500,
        "reset": "weekly",
    },
]

# Объединённый пул (для поиска по ключу)
ALL_QUESTS: Dict[str, QuestDef] = {q["key"]: q for q in DAILY_POOL + WEEKLY_POOL}


def get_quest_by_key(key: str) -> QuestDef | None:
    """Ищет квест по ключу."""
    return ALL_QUESTS.get(key)


def total_pages() -> int:
    """Количество страниц (всегда 2: daily + weekly)."""
    return 2
