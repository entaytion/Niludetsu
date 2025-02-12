from typing import List, Dict, Any, Optional
import re
from datetime import datetime, timedelta

class ModRule:
    """Базовый класс для правил модерации"""
    def __init__(self, name: str, description: str, punishment: Dict[int, str]):
        self.name = name
        self.description = description
        self.punishment = punishment  # {нарушение: наказание}
        self.enabled = True
        self.last_update = datetime.now()
        
    async def check(self, content: str, **kwargs) -> bool:
        """Проверка на нарушение правила"""
        raise NotImplementedError
        
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация настроек правила в словарь"""
        return {
            'enabled': self.enabled,
            'last_update': self.last_update.isoformat()
        }
        
    def update_from_dict(self, data: Dict[str, Any]):
        """Обновление настроек правила из словаря"""
        if 'enabled' in data:
            self.enabled = data['enabled']
        if 'last_update' in data:
            self.last_update = datetime.fromisoformat(data['last_update'])

class SpamRule(ModRule):
    """Правило против спама"""
    def __init__(self):
        super().__init__(
            name="Спам",
            description="Запрещен спам, флуд, повторяющиеся сообщения",
            punishment={
                1: "warn",      # Первое нарушение - предупреждение
                2: "mute_1h",   # Второе нарушение - мут на 1 час
                3: "mute_1d",   # Третье нарушение - мут на 1 день
                4: "ban_3d"     # Четвертое нарушение - бан на 3 дня
            }
        )
        self.message_history = {}  # {user_id: [(content, timestamp)]}
        self.spam_threshold = 4    # Количество похожих сообщений
        self.time_window = 30      # Временное окно в секундах
        self.similarity_threshold = 0.85  # Порог схожести сообщений
        
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Вычисляет схожесть двух строк"""
        if not str1 or not str2:
            return 0.0
        
        # Простой алгоритм схожести
        str1 = str1.lower()
        str2 = str2.lower()
        
        if str1 == str2:
            return 1.0
            
        # Если одна строка содержит другую
        if str1 in str2 or str2 in str1:
            return 0.9
            
        # Подсчет общих символов
        common = sum(1 for c in str1 if c in str2)
        total = max(len(str1), len(str2))
        
        return common / total if total > 0 else 0.0
        
    async def check(self, content: str, **kwargs) -> bool:
        if not self.enabled:
            return False
            
        user_id = kwargs.get('user_id')
        current_time = datetime.now()
        
        # Очищаем старые сообщения
        if user_id in self.message_history:
            self.message_history[user_id] = [
                (msg, time) for msg, time in self.message_history[user_id]
                if (current_time - time).total_seconds() < self.time_window
            ]
        else:
            self.message_history[user_id] = []
            
        # Добавляем новое сообщение
        self.message_history[user_id].append((content, current_time))
        
        # Проверяем на спам
        if len(self.message_history[user_id]) >= self.spam_threshold:
            # Проверяем схожесть последних сообщений
            similar_count = 1  # Текущее сообщение уже считается
            last_messages = self.message_history[user_id][-self.spam_threshold:]
            
            for i in range(len(last_messages) - 1):
                for j in range(i + 1, len(last_messages)):
                    if self._calculate_similarity(last_messages[i][0], last_messages[j][0]) >= self.similarity_threshold:
                        similar_count += 1
                        if similar_count >= self.spam_threshold:
                            return True
                            
        return False

class CapsRule(ModRule):
    """Правило против чрезмерного использования капса"""
    def __init__(self):
        super().__init__(
            name="Капс",
            description="Запрещено чрезмерное использование CAPS LOCK",
            punishment={
                1: "warn",      # Первое нарушение - предупреждение
                2: "warn",      # Второе нарушение - предупреждение
                3: "mute_1h",   # Третье нарушение - мут на 1 час
                4: "mute_1d"    # Четвертое нарушение - мут на 1 день
            }
        )
        self.caps_threshold = 0.7  # Процент капса в сообщении
        
    async def check(self, content: str, **kwargs) -> bool:
        if not self.enabled or len(content) < 6:
            return False
            
        caps_count = sum(1 for c in content if c.isupper())
        caps_ratio = caps_count / len(content)
        
        return caps_ratio > self.caps_threshold

class LinksRule(ModRule):
    """Правило против нежелательных ссылок"""
    def __init__(self):
        super().__init__(
            name="Ссылки",
            description="Запрещены ссылки на сторонние серверы и NSFW контент",
            punishment={
                1: "warn",      # Первое нарушение - предупреждение
                2: "mute_1d",   # Второе нарушение - мут на 1 день
                3: "ban_3d",    # Третье нарушение - бан на 3 дня
                4: "ban_7d"     # Четвертое нарушение - бан на 7 дней
            }
        )
        self.discord_invite_pattern = r'discord\.gg/\w+'
        self.url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        self.allowed_domains = ['discord.com', 'discordapp.com', 'imgur.com', 'youtube.com']
        
    async def check(self, content: str, **kwargs) -> bool:
        if not self.enabled:
            return False
            
        # Проверяем на инвайты Discord
        if re.search(self.discord_invite_pattern, content):
            return True
            
        # Проверяем остальные ссылки
        urls = re.finditer(self.url_pattern, content)
        for url in urls:
            url_str = url.group()
            if not any(domain in url_str for domain in self.allowed_domains):
                return True
                
        return False

class BadWordsRule(ModRule):
    """Правило против нецензурной лексики"""
    def __init__(self):
        super().__init__(
            name="Нецензурная лексика",
            description="Запрещено использование нецензурной лексики и оскорблений",
            punishment={
                1: "warn",      # Первое нарушение - предупреждение
                2: "mute_1h",   # Второе нарушение - мут на 1 час
                3: "mute_1d",   # Третье нарушение - мут на 1 день
                4: "ban_3d"     # Четвертое нарушение - бан на 3 дня
            }
        )
        self.bad_words = [
            "хуй", "пизда", "ебать", "блять", "сука",
            "пидор", "хуесос", "пидорас", "ебанутый", "ебаный",
            "нахуй", "пошелнахуй", "похуй", "нахер", "бля"
        ]
        
    async def check(self, content: str, **kwargs) -> bool:
        if not self.enabled:
            return False
            
        content = content.lower()
        return any(word in content for word in self.bad_words)

class MentionSpamRule(ModRule):
    """Правило против спама упоминаниями"""
    def __init__(self):
        super().__init__(
            name="Спам упоминаниями",
            description="Запрещен спам упоминаниями пользователей и ролей",
            punishment={
                1: "warn",      # Первое нарушение - предупреждение
                2: "mute_1h",   # Второе нарушение - мут на 1 час
                3: "mute_1d",   # Третье нарушение - мут на 1 день
                4: "ban_3d"     # Четвертое нарушение - бан на 3 дня
            }
        )
        self.mention_threshold = 5  # Максимальное количество упоминаний
        
    async def check(self, content: str, **kwargs) -> bool:
        if not self.enabled:
            return False
            
        mention_count = content.count('@')
        return mention_count > self.mention_threshold

class EmoteSpamRule(ModRule):
    """Правило против спама эмодзи"""
    def __init__(self):
        super().__init__(
            name="Спам эмодзи",
            description="Запрещен спам эмодзи и реакциями",
            punishment={
                1: "warn",      # Первое нарушение - предупреждение
                2: "warn",      # Второе нарушение - предупреждение
                3: "mute_1h",   # Третье нарушение - мут на 1 час
                4: "mute_1d"    # Четвертое нарушение - мут на 1 день
            }
        )
        self.emote_threshold = 5  # Максимальное количество эмодзи
        self.emote_pattern = r'<a?:\w+:\d+>|[\U0001F300-\U0001F9FF]'
        
    async def check(self, content: str, **kwargs) -> bool:
        if not self.enabled:
            return False
            
        emote_count = len(re.findall(self.emote_pattern, content))
        return emote_count > self.emote_threshold

class NewlineSpamRule(ModRule):
    """Правило против спама переносами строк"""
    def __init__(self):
        super().__init__(
            name="Спам переносами",
            description="Запрещен спам переносами строк",
            punishment={
                1: "warn",      # Первое нарушение - предупреждение
                2: "warn",      # Второе нарушение - предупреждение
                3: "mute_1h",   # Третье нарушение - мут на 1 час
                4: "mute_1d"    # Четвертое нарушение - мут на 1 день
            }
        )
        self.newline_threshold = 10  # Максимальное количество переносов строк
        
    async def check(self, content: str, **kwargs) -> bool:
        if not self.enabled:
            return False
            
        newline_count = content.count('\n')
        return newline_count > self.newline_threshold 