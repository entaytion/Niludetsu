from typing import List, Dict, Any, Optional
import re
from datetime import datetime, timedelta

class ModRule:
    """Базовый класс для правил модерации"""
    def __init__(self, name: str, description: str, punishment: Dict[int, str]):
        self.name = name
        self.description = description
        self.punishment = punishment  # {нарушение: наказание}
        
    async def check(self, content: str, **kwargs) -> bool:
        """Проверка на нарушение правила"""
        raise NotImplementedError

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
        self.spam_threshold = 5    # Количество похожих сообщений
        self.time_window = 60      # Временное окно в секундах
        
    async def check(self, content: str, **kwargs) -> bool:
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
        if len(content) < 6:  # Игнорируем короткие сообщения
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
        # Загружаем список плохих слов
        self.bad_words = [
            "плохое_слово_1",
            "плохое_слово_2",
            # Добавьте свой список плохих слов
        ]
        
    async def check(self, content: str, **kwargs) -> bool:
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
        newline_count = content.count('\n')
        return newline_count > self.newline_threshold 