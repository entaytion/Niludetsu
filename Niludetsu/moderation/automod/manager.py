"""
Менеджер для работы с настройками автомодерации в Supabase
"""
from Niludetsu import database
from Niludetsu.config import SERVERS
from typing import Dict

MAIN_SERVER_ID = str(SERVERS["MAIN_ID"])

# Дефолтные настройки для всех правил автомода
DEFAULT_RULES = {
    "bad_words": {
        "is_enabled": False,
        "whitelist": [],
        "ignored_channels": [],
        "action": "warn"
    },
    "caps_lock": {
        "is_enabled": False,
        "whitelist": [],
        "ignored_channels": [],
        "limit": 70,
        "action": "warn"
    },
    "custom_words": {
        "is_enabled": False,
        "whitelist": [],
        "ignored_channels": [],
        "words": [],
        "action": "warn"
    },
    "invites": {
        "is_enabled": False,
        "whitelist": [],
        "ignored_channels": [],
        "action": "ban"
    },
    "links": {
        "is_enabled": False,
        "whitelist": [],
        "ignored_channels": [],
        "action": "warn"
    },
    "repeated_text": {
        "is_enabled": False,
        "whitelist": [],
        "ignored_channels": [],
        "limit": 5,
        "action": "warn"
    },
    "spam": {
        "is_enabled": False,
        "whitelist": [],
        "ignored_channels": [],
        "limit": 5,
        "action": "warn"
    }
}

class AutoModManager:
    """Менеджер для работы с настройками автомодерации"""

    def __init__(self):
        self.db = database
        self.guild_id = MAIN_SERVER_ID

    async def get_settings(self) -> Dict:
        """
        Получает все настройки автомодерации для гильдии
        Возвращает словарь с настройками всех правил
        """
        row = await self.db.get_row("automoderation", guild_id=self.guild_id, key="settings")

        if row and row.get('value'):
            # Если данные есть в БД, возвращаем их
            return dict(row['value'])
        else:
            # Если данных нет, создаем дефолтные настройки
            await self.create_default_settings()
            return DEFAULT_RULES.copy()

    async def get_rule(self, rule_name: str) -> Dict:
        """
        Получает настройки конкретного правила

        Args:
            rule_name: Название правила (bad_words, caps_lock, и т.д.)

        Returns:
            Словарь с настройками правила
        """
        settings = await self.get_settings()
        return settings.get(rule_name, DEFAULT_RULES.get(rule_name, {}))

    async def update_rule(self, rule_name: str, rule_data: Dict) -> bool:
        """
        Обновляет настройки конкретного правила

        Args:
            rule_name: Название правила
            rule_data: Новые данные правила

        Returns:
            True если обновление успешно
        """
        # Получаем текущие настройки
        settings = await self.get_settings()

        # Обновляем конкретное правило
        settings[rule_name] = rule_data

        # Сохраняем обратно в БД
        return await self.save_settings(settings)

    async def save_settings(self, settings: Dict) -> bool:
        """
        Сохраняет все настройки автомодерации

        Args:
            settings: Полный словарь настроек всех правил

        Returns:
            True если сохранение успешно
        """
        try:
            # Используем upsert для вставки или обновления
            await self.db.upsert(
                "automoderation",
                {
                    "guild_id": self.guild_id,
                    "key": "settings",
                    "value": settings
                },
                on_conflict="guild_id"
            )
            return True
        except Exception as e:
            print(f"❌ Ошибка сохранения настроек автомода: {e}")
            return False

    async def create_default_settings(self) -> bool:
        """
        Создает дефолтные настройки автомодерации в БД

        Returns:
            True если создание успешно
        """
        return await self.save_settings(DEFAULT_RULES.copy())

    async def toggle_rule(self, rule_name: str) -> bool:
        """
        Переключает состояние правила (включено/выключено)

        Args:
            rule_name: Название правила

        Returns:
            Новое состояние правила (True = включено)
        """
        rule_data = await self.get_rule(rule_name)
        rule_data['is_enabled'] = not rule_data.get('is_enabled', False)
        await self.update_rule(rule_name, rule_data)
        return rule_data['is_enabled']

    async def add_ignored_channel(self, rule_name: str, channel_id: str) -> bool:
        """
        Добавляет канал в список игнорируемых для правила

        Args:
            rule_name: Название правила
            channel_id: ID канала

        Returns:
            True если добавление успешно
        """
        rule_data = await self.get_rule(rule_name)

        if 'ignored_channels' not in rule_data:
            rule_data['ignored_channels'] = []

        if channel_id not in rule_data['ignored_channels']:
            rule_data['ignored_channels'].append(channel_id)
            return await self.update_rule(rule_name, rule_data)

        return False

    async def remove_ignored_channel(self, rule_name: str, channel_id: str) -> bool:
        """
        Удаляет канал из списка игнорируемых для правила

        Args:
            rule_name: Название правила
            channel_id: ID канала

        Returns:
            True если удаление успешно
        """
        rule_data = await self.get_rule(rule_name)

        if 'ignored_channels' in rule_data and channel_id in rule_data['ignored_channels']:
            rule_data['ignored_channels'].remove(channel_id)
            return await self.update_rule(rule_name, rule_data)

        return False

    async def get_enabled_rules(self) -> Dict:
        """
        Получает только включенные правила

        Returns:
            Словарь с включенными правилами
        """
        all_settings = await self.get_settings()
        return {
            rule_name: rule_data 
            for rule_name, rule_data in all_settings.items() 
            if rule_data.get('is_enabled', False)
        }

