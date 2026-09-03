from __future__ import annotations

import asyncio
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

import discord

from ...tools.Patterns import PatternChecker

if TYPE_CHECKING:
    import aiohttp


class AutoModRuleType(str, Enum):
    LINKS         = "links"
    INVITES       = "invites"
    SPAM          = "spam"
    BAD_WORDS     = "bad_words"
    REPEATED_TEXT = "repeated_text"
    CAPS_LOCK     = "caps_lock"
    CUSTOM_WORDS  = "custom_words"

    @property
    def label(self) -> str:
        return {
            self.LINKS:         "Ссылки",
            self.INVITES:       "Инвайты",
            self.SPAM:          "Спам",
            self.BAD_WORDS:     "Запрещённые слова",
            self.REPEATED_TEXT: "Повтор текста",
            self.CAPS_LOCK:     "Капслок",
            self.CUSTOM_WORDS:  "Кастомные слова",
        }[self]


_INVISIBLE = re.compile(
    r"[\u200b\u200c\u200d\u200e\u200f\u2060-\u2064\ufeff\u034f\u00ad]"
)
_MARKDOWN_URL = re.compile(r"\[.*?\]\((.+?)\)")
_DISCORD_INVITE = re.compile(
    r"(?:https?://)?(?:www\.|canary\.|ptb\.)?(?:discord(?:\.gg|(?:app)?\.com/invite|\.me)"
    r"|dsc\.gg|invite\.gg)/([^\s/]+)",
    re.I,
)
_BOT_INVITE = re.compile(
    r"(?:https?://)?(?:www\.|canary\.|ptb\.)?discord(?:app)?\.com/(?:api/)?oauth2/authorize\?[^\s]+",
    re.I,
)
_OBFUSCATED_INVITE = re.compile(r"discord\s*\.\s*gg\s*/\s*([^\s]+)", re.I)
_URL = re.compile(r"https?://[^\s)\]>]+", re.I)
_BARE_URL = re.compile(
    r"(?:https?://|www\.)[^\s]+|(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?:/[^\s]*)?",
    re.I,
)
_DISCORD_HOST = re.compile(r"discord\.(gg|com|me|io)", re.I)
_DISCORD_CDN = frozenset(
    {"cdn.discordapp.com", "media.discordapp.net",
     "images-ext-1.discordapp.net", "images-ext-2.discordapp.net"}
)


def _clean(text: str) -> str:
    return _INVISIBLE.sub("", text)


def _all_texts(content: str) -> list[str]:
    cleaned = _clean(content)
    texts = [cleaned]
    for url in _MARKDOWN_URL.findall(content):
        texts.append(_clean(url))
    return texts


@dataclass
class RuleConfig:
    is_enabled:       bool      = False
    whitelist:        list[str] = field(default_factory=list)
    ignored_channels: list[str] = field(default_factory=list)
    action:           str       = "warn"
    limit:            int       = 5


class AutoModRule:

    rule_type: AutoModRuleType

    def __init__(self, cfg: RuleConfig) -> None:
        self.cfg = cfg

    def _base_ok(self, message: discord.Message) -> bool:
        return (
            self.cfg.is_enabled
            and str(message.channel.id) not in self.cfg.ignored_channels
        )

    async def check(self, message: discord.Message, **kw) -> bool:
        raise NotImplementedError


class LinksRule(AutoModRule):
    rule_type = AutoModRuleType.LINKS

    async def check(self, message: discord.Message, **_) -> bool:
        if not self._base_ok(message):
            return False

        sources = [message.content]
        if message.reference and isinstance(message.reference.resolved, discord.Message):
            sources.append(message.reference.resolved.content)

        for src in sources:
            for text in _all_texts(src):
                for url in _BARE_URL.findall(text):
                    lo = url.lower()
                    if _DISCORD_HOST.search(lo):
                        continue
                    if any(cdn in lo for cdn in _DISCORD_CDN):
                        continue
                    if not any(w in lo for w in self.cfg.whitelist):
                        return True
        return False


class InvitesRule(AutoModRule):
    rule_type = AutoModRuleType.INVITES

    async def check(
        self,
        message: discord.Message,
        http_session: "aiohttp.ClientSession | None" = None,
    ) -> bool:
        if not self._base_ok(message):
            return False

        sources = [message.content]
        if message.reference and isinstance(message.reference.resolved, discord.Message):
            sources.append(message.reference.resolved.content)

        for src in sources:
            if await self._scan(src, message, http_session):
                return True
        return False

    async def _scan(
        self,
        content: str,
        message: discord.Message,
        session: "aiohttp.ClientSession | None",
    ) -> bool:
        for text in _all_texts(content):
            if await self._has_invite(text, message):
                return True

        if session:
            urls = _URL.findall(content)
            checked = 0
            for url in urls:
                if checked >= 3:
                    break
                lo = url.lower()
                if "discord.gg/" in lo or "discord.com/invite" in lo:
                    continue
                final = await self._resolve(url, session)
                if final != url and await self._has_invite(final, message):
                    return True
                checked += 1
        return False

    async def _has_invite(self, text: str, message: discord.Message) -> bool:
        if _BOT_INVITE.search(text) or _OBFUSCATED_INVITE.search(text):
            return True

        matches = list(_DISCORD_INVITE.finditer(text))
        if not matches:
            return False

        vanity = getattr(message.guild, "vanity_url_code", None) if message.guild else None

        server_invites: set[str] = set()
        if message.guild and message.guild.me.guild_permissions.manage_guild:
            try:
                server_invites = {inv.code for inv in await message.guild.invites()}
            except Exception:
                pass

        for m in matches:
            code = m.group(1).split("/")[0].split("?")[0]
            if code in self.cfg.whitelist:
                continue
            if vanity and code == vanity:
                continue
            if code in server_invites:
                continue
            return True
        return False

    @staticmethod
    async def _resolve(url: str, session: "aiohttp.ClientSession") -> str:
        try:
            async with session.head(url, allow_redirects=True, timeout=2.0) as r:
                return str(r.url)
        except Exception:
            return url


class CapsLockRule(AutoModRule):
    rule_type = AutoModRuleType.CAPS_LOCK

    async def check(self, message: discord.Message, **_) -> bool:
        if not self._base_ok(message):
            return False
        letters = [c for c in message.content if c.isalpha()]
        if len(letters) < 10:
            return False
        threshold = self.cfg.limit / 100
        return sum(c.isupper() for c in letters) / len(letters) > threshold


class SpamRule(AutoModRule):
    rule_type = AutoModRuleType.SPAM

    def __init__(self, cfg: RuleConfig) -> None:
        super().__init__(cfg)
        self._history: dict[int, list[float]] = {}

    async def check(self, message: discord.Message, **_) -> bool:
        if not self._base_ok(message):
            return False
        uid = message.author.id
        now = asyncio.get_event_loop().time()
        bucket = [t for t in self._history.get(uid, []) if now - t < 5.0]
        bucket.append(now)
        self._history[uid] = bucket
        return len(bucket) > self.cfg.limit


class BadWordsRule(AutoModRule):
    rule_type = AutoModRuleType.BAD_WORDS

    _BASE_WORDS = {"хохол"}
    _VARIATIONS = {
        "хохол": [
            "хахол", "хихол", "хохлы", "хахлы", "хiхол",
            "хохла", "хахла", "хохлина", "хохляра",
            "хохлик", "хахлик", "хохлята", "хахляра",
        ]
    }
    _initialized = False

    def __init__(self, cfg: RuleConfig) -> None:
        super().__init__(cfg)
        if not BadWordsRule._initialized:
            for word, variants in self._VARIATIONS.items():
                PatternChecker.add_word_variations(word, variants)
            BadWordsRule._initialized = True

    async def check(self, message: discord.Message, **_) -> bool:
        if not self._base_ok(message):
            return False
        text = message.content
        return any(PatternChecker.check_word(text, w) for w in self._BASE_WORDS)


class RepeatedTextRule(AutoModRule):
    rule_type = AutoModRuleType.REPEATED_TEXT

    def __init__(self, cfg: RuleConfig) -> None:
        super().__init__(cfg)
        self._history: dict[int, list[str]] = {}

    async def check(self, message: discord.Message, **_) -> bool:
        if not self._base_ok(message):
            return False

        content = message.content
        uid = message.author.id

        if "\n" in content:
            lines = [
                re.sub(r"\W+", "", ln.strip().lower())
                for ln in content.split("\n")
                if len(ln.strip()) > 15
            ]
            if lines:
                counts: dict[str, int] = {}
                for ln in lines:
                    counts[ln] = counts.get(ln, 0) + 1
                dups = {ln: c for ln, c in counts.items() if c >= 3}
                if dups:
                    dup_chars = sum(len(ln) * c for ln, c in dups.items())
                    total = sum(len(ln) for ln in lines)
                    if total and dup_chars / total > 0.4:
                        return True

        words = [w for w in re.findall(r"\b\w+\b", content.lower()) if len(w) >= 4]
        wcounts: dict[str, int] = {}
        for w in words:
            wcounts[w] = wcounts.get(w, 0) + 1
        if any(c >= 4 for c in wcounts.values()):
            return True

        history = self._history.get(uid, [])
        if len(content) > 20:
            norm = re.sub(r"\W+", "", content.lower())
            for prev in history:
                if prev == content:
                    return True
                if len(prev) > 20:
                    pnorm = re.sub(r"\W+", "", prev.lower())
                    if pnorm == norm:
                        return True
                    if len(pnorm) > 30 and len(norm) > 30:
                        shorter, longer = (
                            (norm, pnorm) if len(norm) <= len(pnorm) else (pnorm, norm)
                        )
                        matches = sum(a == b for a, b in zip(shorter, longer))
                        if matches / len(longer) > 0.9:
                            return True

        self._history[uid] = (history + [content])[-5:]
        return False


class CustomWordsRule(AutoModRule):
    rule_type = AutoModRuleType.CUSTOM_WORDS

    _BASE_WORDS = {"okx", "окх"}

    def __init__(self, cfg: RuleConfig) -> None:
        super().__init__(cfg)
        self._violations: dict[int, int] = {}

    async def check(self, message: discord.Message, **_) -> bool:
        if not self._base_ok(message):
            return False

        words = self._BASE_WORDS | set(self.cfg.whitelist)
        content = message.content.lower()

        for word in words:
            if PatternChecker.check_custom_word(content, word):
                uid = message.author.id
                self._violations[uid] = self._violations.get(uid, 0) + 1
                if self._violations[uid] == 1:
                    try:
                        await message.delete()
                    except Exception:
                        pass
                    return False
                return True
        return False


_RULE_CLASSES: dict[AutoModRuleType, type[AutoModRule]] = {
    AutoModRuleType.LINKS:         LinksRule,
    AutoModRuleType.INVITES:       InvitesRule,
    AutoModRuleType.SPAM:          SpamRule,
    AutoModRuleType.BAD_WORDS:     BadWordsRule,
    AutoModRuleType.REPEATED_TEXT: RepeatedTextRule,
    AutoModRuleType.CAPS_LOCK:     CapsLockRule,
    AutoModRuleType.CUSTOM_WORDS:  CustomWordsRule,
}


def build_rule(rule_type: AutoModRuleType, cfg: RuleConfig) -> AutoModRule:
    cls = _RULE_CLASSES[rule_type]
    return cls(cfg)
