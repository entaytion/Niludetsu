import discord
from datetime import datetime
from discord.ext import commands
from Niludetsu import safe_delete
from Niludetsu.config import SERVERS
from Niludetsu.moderation.automod import AutoModRuleType, LinksRule, InvitesRule, CapsLockRule, BadWordsRule, AutoModManager
from Niludetsu.moderation.config import ActionType
from Niludetsu.moderation.manager import ModerationManager
from typing import Optional, Dict

class AutoModListener(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.automod_manager = AutoModManager()
        self.mod_manager = ModerationManager(bot)  

        self._rules_cache: Optional[Dict] = None
        self._cache_time: Optional[datetime] = None
        self._cache_ttl = 300  # 5 минут

        self.spam_history = {}  # {user_id: [timestamps]}
        self.custom_words_violations = {}  # {user_id: count}
        self.repeated_text_history = {}  # {user_id: [last_messages]}

    async def _get_rules_cached(self) -> Dict:
        """Получает правила с кэшированием (решает проблему запросов к БД на каждое сообщение)"""
        now = datetime.now()

        # Если кэш валиден, возвращаем его
        if self._rules_cache and self._cache_time:
            if (now - self._cache_time).total_seconds() < self._cache_ttl:
                return self._rules_cache

        # Иначе обновляем кэш
        self._rules_cache = await self.automod_manager.get_enabled_rules()
        self._cache_time = now
        return self._rules_cache

    def invalidate_cache(self):
        """Сбрасывает кэш (вызывается при изменении настроек через /automod)"""
        self._rules_cache = None
        self._cache_time = None

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Игнорируем ботов и не основной сервер
        if message.author.bot or not message.guild or message.guild.id != SERVERS["MAIN_ID"]:
            return

        rules = await self._get_rules_cached()
        if not rules:
            return

        # Проверяем каждое правило
        for rule_type, rule_data in rules.items():
            if not rule_data["is_enabled"]:
                continue

            # Пропускаем игнорируемые каналы
            if str(message.channel.id) in rule_data.get("ignored_channels", []):
                continue

            if await self._check_rule(rule_type, rule_data, message):
                # Удаляем нарушающее сообщение
                deleted = await safe_delete(message)
                if deleted:
                    print(f"🗑️ AutoMod: Удалено сообщение от {message.author} в {message.channel} за нарушение правила {rule_type}")
                else:
                    print(f"⚠️ AutoMod: Не удалось удалить сообщение в {message.channel}")

                # Сохраняем роли пользователя для софтбана
                roles = [role.id for role in message.author.roles if role.name != "@everyone"]

                if rule_type == AutoModRuleType.INVITES.value:
                    # Для инвайтов: предупреждение + бан
                    await self.mod_manager.execute(
                        action_type=ActionType.WARN,
                        guild=message.guild,
                        target=message.author,
                        moderator=message.guild.me,
                        reason="1.4",
                        channel=message.channel,
                        metadata={"roles": roles}
                    )
                    await self.mod_manager.execute(
                        action_type=ActionType.BAN,
                        guild=message.guild,
                        target=message.author,
                        moderator=message.guild.me,
                        reason="1.4",
                        channel=message.channel,
                        metadata={"roles": roles}
                    )
                else:
                    # Для остальных нарушений: только предупреждение
                    await self.mod_manager.execute(
                        action_type=ActionType.WARN,
                        guild=message.guild,
                        target=message.author,
                        moderator=message.guild.me,
                        reason=f"Автомодерация: {rule_type}",
                        channel=message.channel,
                        metadata={"roles": roles}
                    )

                break  # Останавливаемся на первом нарушении

    async def _check_rule(self, rule_type, rule_data, message):
        """Проверяет сообщение по типу правила (с поддержкой состояния)"""
        # Используем соответствующий класс для проверки
        rule_map = {
            AutoModRuleType.LINKS.value: LinksRule,
            AutoModRuleType.INVITES.value: InvitesRule,
            AutoModRuleType.CAPS_LOCK.value: CapsLockRule,
            AutoModRuleType.SPAM.value: self._check_spam_with_state,  
            AutoModRuleType.BAD_WORDS.value: BadWordsRule,
            AutoModRuleType.REPEATED_TEXT.value: self._check_repeated_with_state,  
            AutoModRuleType.CUSTOM_WORDS.value: self._check_custom_words_with_state,  
        }

        handler = rule_map.get(rule_type)
        if not handler:
            return False

        # Если это класс правила (не функция), создаём экземпляр
        if isinstance(handler, type):
            rule_obj = handler(
                guild_id=str(message.guild.id),
                is_enabled=rule_data.get("is_enabled", False),
                whitelist=rule_data.get("whitelist", []),
                ignored_channels=rule_data.get("ignored_channels", [])
            )
            return await rule_obj.check_message(message)

        # Иначе это функция с состоянием
        return await handler(rule_data, message)

    async def _check_spam_with_state(self, rule_data, message):
        """Проверка спама с сохранением истории сообщений"""
        from Niludetsu.tools.Time import TimeService
        _time = TimeService()

        max_messages = rule_data.get("limit", 5)
        interval = 5  # секунд

        now = _time.now()
        user_id = message.author.id

        # Инициализируем историю
        if user_id not in self.spam_history:
            self.spam_history[user_id] = []

        # Очищаем старые записи
        active_timestamps = [
            ts for ts in self.spam_history[user_id]
            if _time.seconds_between(now, ts, absolute=True) <= interval
        ]

        if not active_timestamps and user_id in self.spam_history:
            del self.spam_history[user_id]
            active_timestamps = []
            
        self.spam_history.setdefault(user_id, []).extend(active_timestamps)
        
        # Добавляем текущее сообщение
        self.spam_history[user_id].append(now)

        # Проверяем превышение лимита
        return len(self.spam_history[user_id]) > max_messages

    async def _check_repeated_with_state(self, rule_data, message):
        """Проверка повторяющегося текста с сохранением истории"""
        import re

        user_id = message.author.id
        content = message.content

        # Инициализируем историю
        if user_id not in self.repeated_text_history:
            self.repeated_text_history[user_id] = []

        history = self.repeated_text_history[user_id]

        # 1. Проверка повторяющихся строк внутри сообщения
        if '\n' in content:
            lines = [re.sub(r'\W+', '', line.strip().lower()) for line in content.split('\n') if len(line.strip()) > 15]
            if lines:
                line_counts = {}
                for line in lines:
                    line_counts[line] = line_counts.get(line, 0) + 1

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
        if len(content) > 20:
            norm_current = re.sub(r'\W+', '', content.lower())

            for prev in history:
                if prev == content:
                    return True

                if len(prev) > 20:
                    norm_prev = re.sub(r'\W+', '', prev.lower())

                    if norm_prev == norm_current:
                        return True

                    if len(norm_prev) > 30 and len(norm_current) > 30:
                        shorter = min(norm_prev, norm_current, key=len)
                        longer = max(norm_prev, norm_current, key=len)
                        matches = sum(1 for i in range(len(shorter)) if shorter[i] == longer[i])
                        if matches / len(longer) > 0.9:
                            return True

        # Обновляем историю (последние 5 сообщений)
        self.repeated_text_history[user_id] = (history + [content])[-5:]
        return False

    async def _check_custom_words_with_state(self, rule_data, message):
        """Проверка кастомных слов с подсчётом нарушений"""
        from Niludetsu.tools.Patterns import PatternChecker

        custom_words = {"okx", "окх"}
        content = message.content.lower()

        for word in custom_words:
            if PatternChecker.check_custom_word(content, word):
                user_id = str(message.author.id)
                self.custom_words_violations[user_id] = self.custom_words_violations.get(user_id, 0) + 1

                # Первое нарушение: просто удалить сообщение
                if self.custom_words_violations[user_id] == 1:
                    try:
                        await message.delete()
                    except Exception:
                        pass
                    return False  # Не выдаём наказание

                # Второе и далее: выдаём наказание
                return True

        return False

    async def check_message_violations(self, message: discord.Message) -> bool:
        """
        Проверяет сообщение на нарушения автомода без применения наказаний.
        Возвращает True если есть нарушение, False если сообщение чистое.
        """
        if message.author.bot or not message.guild or message.guild.id != SERVERS["MAIN_ID"]:
            return False

        rules = await self._get_rules_cached()
        if not rules:
            return False

        for rule_type, rule_data in rules.items():
            if not rule_data["is_enabled"]:
                continue

            if str(message.channel.id) in rule_data.get("ignored_channels", []):
                continue

            if await self._check_rule(rule_type, rule_data, message):
                return True

        return False

async def setup(bot):
    await bot.add_cog(AutoModListener(bot))

