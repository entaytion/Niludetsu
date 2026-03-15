import discord, re
from enum import Enum
from Niludetsu.tools.Patterns import PatternChecker
from Niludetsu.tools.Time import TimeService
from typing import List

_time = TimeService()

class AutoModRuleType(Enum):
    """Типы правил автомодерации"""
    LINKS = "links"
    INVITES = "invites"
    SPAM = "spam"
    BAD_WORDS = "bad_words"
    REPEATED_TEXT = "repeated_text"
    CAPS_LOCK = "caps_lock"
    CUSTOM_WORDS = "custom_words"

class AutoModRule:
    """Базовый класс для правил автомодерации"""
    def __init__(
        self,
        guild_id: str,
        rule_type: AutoModRuleType,
        is_enabled: bool = False,
        whitelist: List[str] = None,
        ignored_channels: List[str] = None,
        description: str = None
    ):
        self.guild_id = guild_id
        self.rule_type = rule_type
        self.is_enabled = is_enabled
        self.whitelist = whitelist or []
        self.ignored_channels = ignored_channels or []
        self.description = description or self.get_default_description()

    async def check_message(self, message: discord.Message) -> bool:
        """Базовая проверка: правило включено и канал не игнорируется"""
        return self.is_enabled and str(message.channel.id) not in self.ignored_channels

    def get_default_description(self) -> str:
        """Возвращает описание правила по умолчанию"""
        descriptions = {
            AutoModRuleType.LINKS: "Блокировка ссылок",
            AutoModRuleType.INVITES: "Блокировка Discord инвайтов",
            AutoModRuleType.SPAM: "Защита от спама",
            AutoModRuleType.BAD_WORDS: "Фильтр мата",
            AutoModRuleType.REPEATED_TEXT: "Блокировка повторов",
            AutoModRuleType.CAPS_LOCK: "Блокировка КАПСА",
            AutoModRuleType.CUSTOM_WORDS: "Фильтр кастомных слов"
        }
        return descriptions.get(self.rule_type, "Правило автомодерации")

class LinksRule(AutoModRule):
    """Правило для проверки ссылок"""

    # Встроенные исключения (Discord CDN)
    DISCORD_CDN = {'cdn.discordapp.com', 'media.discordapp.net', 'images-ext-1.discordapp.net', 'images-ext-2.discordapp.net'}

    def __init__(self, *args, **kwargs):
        kwargs['rule_type'] = AutoModRuleType.LINKS
        super().__init__(*args, **kwargs)
        # Ловит ссылки с http://, https:// и без протокола (www., domain.com)
        self.url_pattern = re.compile(
            r'(?:https?://|www\.)[^\s]+|(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?:/[^\s]*)?',
            re.IGNORECASE
        )
        self.discord_pattern = re.compile(r'discord\.(?:gg|com|me|io)', re.IGNORECASE)

    async def check_message(self, message: discord.Message) -> bool:
        if not await super().check_message(message):
            return False

        # Проверяем основное сообщение и пересланное
        raw_contents = [message.content]
        if message.reference and isinstance(message.reference.resolved, discord.Message):
            raw_contents.append(message.reference.resolved.content)

        # Собираем все тексты для проверки (оригинал + URL из markdown)
        contents = []
        for raw in raw_contents:
            contents.append(raw)
            for md_url in InvitesRule._MARKDOWN_LINK_RE.findall(raw):
                contents.append(md_url)

        for content in contents:
            urls = self.url_pattern.findall(content)
            if not urls:
                continue

            for url in urls:
                url_lower = url.lower()

                # Пропускаем Discord ссылки (для них есть InvitesRule)
                if self.discord_pattern.search(url_lower):
                    continue

                # Пропускаем Discord CDN
                if any(cdn in url_lower for cdn in self.DISCORD_CDN):
                    continue

                # Проверяем whitelist
                if not any(allowed in url_lower for allowed in self.whitelist):
                    return True

        return False

import aiohttp

class InvitesRule(AutoModRule):
    """Правило для проверки приглашений Discord и ботов"""

    # Zero-width и невидимые символы, которыми обходят фильтры
    _INVISIBLE_RE = re.compile(r'[\u200b\u200c\u200d\u200e\u200f\u2060\u2061\u2062\u2063\u2064\ufeff\u034f\u00ad]')
    # Markdown-ссылки [text](url) — вытаскиваем url
    _MARKDOWN_LINK_RE = re.compile(r'\[.*?\]\((.+?)\)')

    def __init__(self, *args, **kwargs):
        kwargs['rule_type'] = AutoModRuleType.INVITES
        super().__init__(*args, **kwargs)
        # Паттерн для серверных инвайтов (discord.gg, discord.com/invite, discord.me, dsc.gg)
        self.invite_pattern = re.compile(
            r'(?:https?://)?(?:www\.|canary\.|ptb\.)?(?:discord(?:\.gg|(?:app)?\.com/invite|\.me)|dsc\.gg|invite\.gg)/([^\s]+)/?',
            re.IGNORECASE
        )
        # Паттерн для bot invite (OAuth2)
        self.bot_invite_pattern = re.compile(
            r'(?:https?://)?(?:www\.|canary\.|ptb\.)?discord(?:app)?\.com/(?:api/)?oauth2/authorize\?([^\s]+)/?',
            re.IGNORECASE
        )
        # Паттерн для обфусцированных вариантов типа "discord . gg / code" (с пробелами)
        self.obfuscated_invite_pattern = re.compile(
            r'discord\s*\.\s*gg\s*/\s*([^\s]+)',
            re.IGNORECASE
        )
        # Паттерн для любых URL (для проверки шортенеров)
        self.any_url_pattern = re.compile(
            r'https?://[^\s)\]>]+',
            re.IGNORECASE
        )

    @staticmethod
    def _normalize(content: str) -> str:
        """Убирает zero-width символы и извлекает URL из markdown."""
        content = InvitesRule._INVISIBLE_RE.sub('', content)
        return content

    @staticmethod
    def _extract_all_texts(content: str) -> list[str]:
        """Возвращает список текстов для проверки: оригинал + URL из markdown."""
        normalized = InvitesRule._normalize(content)
        texts = [normalized]
        for md_url in InvitesRule._MARKDOWN_LINK_RE.findall(content):
            texts.append(InvitesRule._normalize(md_url))
        return texts

    @staticmethod
    async def _resolve_url(url: str) -> str:
        """Переходит по ссылке чтобы раскрыть сокращенные URL (bit.ly, url-shortener.me и тд)."""
        try:
            async with aiohttp.ClientSession() as session:
                # Делаем HEAD запрос
                async with session.head(url, allow_redirects=True, timeout=2.0) as resp:
                    return str(resp.url)
        except:
            pass
        return url

    async def check_message(self, message: discord.Message) -> bool:
        if not await super().check_message(message):
            return False

        # Проверяем основное сообщение и пересланное
        if await self._check_content(message, message.content):
            return True

        if message.reference and isinstance(message.reference.resolved, discord.Message):
            if await self._check_content(message, message.reference.resolved.content):
                return True

        return False

    async def _check_content(self, message: discord.Message, content: str) -> bool:
        texts = self._extract_all_texts(content)

        # 1. Быстрая проверка всех текстов
        for text in texts:
            if await self._contains_invite(text, message):
                return True
                
        # 2. Продвинутая проверка (анти-шортленкинг)
        # Находим все ссылки и резолвим их, чтобы найти спрятанные инвайты
        urls = self.any_url_pattern.findall(content)
        checked_urls = 0
        
        for url in urls:
            if checked_urls >= 3:  # Проверяем максимум 3 урла чтобы не вешать бота
                break
                
            # Пропускаем дискорд ссылки, они уже проверены
            if "discord.gg/" in url.lower() or "discord.com/invite" in url.lower():
                continue
                
            final_url = await self._resolve_url(url)
            if final_url != url:
                if await self._contains_invite(final_url, message):
                    return True
            checked_urls += 1

        return False

    async def _contains_invite(self, text: str, message: discord.Message) -> bool:
        # Проверяем bot invites
        if self.bot_invite_pattern.search(text):
            return True

        # Проверяем обфусцированные варианты
        if self.obfuscated_invite_pattern.search(text):
            return True

        # Проверяем server invites
        invite_matches = list(self.invite_pattern.finditer(text))
        if not invite_matches:
            return False

        vanity_code = message.guild.vanity_url_code if message.guild and hasattr(message.guild, 'vanity_url_code') else None

        for match in invite_matches:
            invite_code = match.group(1).split('/')[0].split('?')[0]

            if invite_code in self.whitelist:
                continue

            if vanity_code and invite_code == vanity_code:
                continue

            if message.guild and message.guild.me.guild_permissions.manage_guild:
                try:
                    invites = await message.guild.invites()
                    if any(invite.code == invite_code for invite in invites):
                        continue
                except Exception:
                    pass

            return True

        return False

class CapsLockRule(AutoModRule):
    """Правило для проверки CAPS LOCK"""
    def __init__(self, *args, threshold: float = 0.7, min_length: int = 10, **kwargs):
        kwargs['rule_type'] = AutoModRuleType.CAPS_LOCK
        super().__init__(*args, **kwargs)
        self.threshold = threshold
        self.min_length = min_length

    async def check_message(self, message: discord.Message) -> bool:
        if not await super().check_message(message):
            return False

        letters = [c for c in message.content if c.isalpha()]

        if len(letters) < self.min_length:
            return False

        caps_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
        return caps_ratio > self.threshold

class SpamRule(AutoModRule):
    """Правило для проверки спама"""
    def __init__(self, *args, max_messages: int = 5, interval: int = 5, **kwargs):
        super().__init__(*args, rule_type=AutoModRuleType.SPAM, **kwargs)
        self.max_messages = max_messages
        self.interval = interval
        self.message_history = {}  # {user_id: [timestamps]}

    async def check_message(self, message: discord.Message) -> bool:
        if not await super().check_message(message):
            return False

        now = _time.now()
        user_id = message.author.id

        # Инициализируем историю
        if user_id not in self.message_history:
            self.message_history[user_id] = []

        # Очищаем старые записи
        self.message_history[user_id] = [
            ts for ts in self.message_history[user_id] 
            if _time.seconds_between(now, ts, absolute=True) <= self.interval
        ]

        # Добавляем текущее сообщение
        self.message_history[user_id].append(now)

        # Проверяем превышение лимита
        return len(self.message_history[user_id]) > self.max_messages

class BadWordsRule(AutoModRule):
    """Правило для проверки запрещенных слов"""

    BAD_WORDS = {"хохол"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, rule_type=AutoModRuleType.BAD_WORDS, **kwargs)

        # Добавляем вариации один раз при инициализации класса
        PatternChecker.add_word_variations("хохол", [
            "хахол", "хихол", "хохлы", "хахлы", "хiхол",
            "хохла", "хахла", "хохлина", "хохляра",
            "хохлик", "хахлик", "хохлята", "хахляра"
        ])

    async def check_message(self, message: discord.Message) -> bool:
        if not await super().check_message(message):
            return False

        return any(PatternChecker.check_word(message.content, word) for word in self.BAD_WORDS)

class RepeatedTextRule(AutoModRule):
    """Правило для проверки повторяющегося текста"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, rule_type=AutoModRuleType.REPEATED_TEXT, **kwargs)
        self.user_messages = {}  # {user_id: [last_5_messages]}

    async def check_message(self, message: discord.Message) -> bool:
        if not await super().check_message(message):
            return False

        content = message.content
        user_id = message.author.id

        # 1. Проверка повторяющихся строк внутри сообщения
        if '\n' in content:
            lines = [re.sub(r'\W+', '', line.strip().lower()) for line in content.split('\n') if len(line.strip()) > 15]
            if lines:
                line_counts = {}
                for line in lines:
                    line_counts[line] = line_counts.get(line, 0) + 1

                # Если есть строки с 3+ повторениями и они составляют >40% сообщения
                duplicates = {line: count for line, count in line_counts.items() if count >= 3}
                if duplicates:
                    duplicate_chars = sum(len(line) * count for line, count in duplicates.items())
                    total_chars = sum(len(line) for line in lines)
                    if duplicate_chars / total_chars > 0.4:
                        return True

        # 2. Проверка повторяющихся слов (4+ раза)
        words = [w for w in re.findall(r'\b\w+\b', content.lower()) if len(w) >= 4]
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1

        if any(count >= 4 for count in word_counts.values()):
            return True

        # 3. Проверка повторения между сообщениями
        if user_id not in self.user_messages:
            self.user_messages[user_id] = []

        history = self.user_messages[user_id]

        # Проверяем идентичные или очень похожие сообщения
        if len(content) > 20:
            norm_current = re.sub(r'\W+', '', content.lower())

            for prev in history:
                if prev == content:  # Полное совпадение
                    return True

                if len(prev) > 20:
                    norm_prev = re.sub(r'\W+', '', prev.lower())

                    # Полное совпадение после нормализации
                    if norm_prev == norm_current:
                        return True

                    # Очень высокое сходство (>90%)
                    if len(norm_prev) > 30 and len(norm_current) > 30:
                        shorter = min(norm_prev, norm_current, key=len)
                        longer = max(norm_prev, norm_current, key=len)
                        matches = sum(1 for i in range(len(shorter)) if shorter[i] == longer[i])
                        if matches / len(longer) > 0.9:
                            return True

        # Обновляем историю (последние 5 сообщений)
        self.user_messages[user_id] = (history + [content])[-5:]

        return False

class CustomWordsRule(AutoModRule):
    """Правило для фильтрации кастомных слов (например, okx)"""

    CUSTOM_WORDS = {"okx", "окх"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, rule_type=AutoModRuleType.CUSTOM_WORDS, **kwargs)
        self.violations = {}  # {user_id: violation_count}

    async def check_message(self, message: discord.Message) -> bool:
        if not await super().check_message(message):
            return False

        # Проверяем кастомные слова с allow_gaps=True (ловит "o k x", "о к х" и т.д.)
        content = message.content.lower()
        for word in self.CUSTOM_WORDS:
            if PatternChecker.check_custom_word(content, word):
                user_id = str(message.author.id)
                self.violations[user_id] = self.violations.get(user_id, 0) + 1

                # Первое нарушение: удаляем сообщение без мута
                if self.violations[user_id] == 1:
                    try:
                        await message.delete()
                    except Exception:
                        pass
                    return False  # Не выдаём наказание

                # Второе и далее: выдаём наказание
                return True

        return False

