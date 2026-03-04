
import re, unicodedata
from functools import lru_cache
from typing import Dict, Iterable, List, Optional, Sequence, Set

ZERO_WIDTH_PATTERN = re.compile(
    r"[\u200B-\u200F\u202A-\u202E\u2060-\u206F\uFEFF]"
)

COMBINING_MARK_PATTERN = re.compile(
    r"[\u0300-\u036F\u0483-\u0489\u1AB0-\u1AFF\u1DC0-\u1DFF\u20D0-\u20FF\u2DE0-\u2DFF\u3099\u309A]"
)

class PatternChecker:
    """
    Расширенный проверщик слов с учётом визуальных замен букв, диакритики и «зашумления» текста.
    """

    LETTER_GROUPS: Sequence[Sequence[str]] = [
        # A / А
        (
            "a", "а", "@", "4", "α", "à", "á", "â", "ã", "ä", "å", "ā", "ă", "ą", "ɑ", "ɐ",
            "ᴀ", "Ａ", "Ａ̄", "𝒶", "𝐚", "𝐀", "𝔞", "𝕒"
        ),
        # B / Б / В
        (
            "b", "б", "в", "6", "8", "ß", "β", "ḅ", "b̄", "ᛒ", "ʙ", "В", "B", "В̄"
        ),
        # V / W
        (
            "v", "w", "vv", "ѵ", "Ѵ", "∨", "√", "\/", "\\/", "ʋ", "v̄", "v̆", "ν"
        ),
        # Г / Ґ / G
        ("г", "ґ", "g", "ɡ", "ġ", "ģ", "ĝ", "ᴑ", "ʛ"),
        # D
        ("d", "д", "∂", "đ", "ď", "ԁ", "d̄"),
        # E / Ё / Є / Э
        (
            "e", "е", "ё", "є", "э", "€", "ē", "é", "è", "ĕ", "ě", "ę", "ė", "ë",
            "Ё", "Е", "Є", "Э"
        ),
        # Ж
        ("ж", "zh", "x", "жж", "ž", "ʒ", "ǯ", "*"),
        # З
        ("з", "3", "z", "ʒ", "ž", "ź", "ż"),
        # И / I
        ("и", "i", "ī", "í", "ĭ", "1", "|", "ɨ"),
        # І / Ї
        ("і", "ї", "i", "ï", "ї̈", "jï", "yi", "1", "l"),
        # Й / J / Y
        ("й", "y", "j", "ĭ", "ŷ", "ɉ"),
        # K / К
        ("k", "к", "κ", "|{", "|<", "<", "ķ", "k̄"),
        # Л / Λ
        ("л", "l", "λ", "ɩ", "ɫ", "ľ", "ļ", "ł"),
        # М / M
        ("м", "m", "^^", "/\\/\\", "ɱ", "ɯ", "м̄"),
        # Н / H / N
        ("н", "h", "n", "|-|", "ń", "ņ", "ñ", "ŋ"),
        # O / O
        (
            "o", "о", "0", "∅", "⊕", "ō", "ó", "ò", "ô", "ö", "õ", "ø", "Ø",
            "ο", "Ο", "Θ", "○"
        ),
        # П / Π
        ("п", "n", "p", "∏", "Π"),
        # P / Р / R
        ("p", "р", "r", "®", "ŕ", "ř", "ρ", "P̄"),
        # C / С / $
        ("c", "с", "s", "$", "©", "ś", "š", "ŝ", "ş", "¢"),
        # T / Т
        ("t", "т", "†", "+", "ţ", "ŧ"),
        # У / Y / U
        ("у", "y", "u", "v", "ū", "ú", "ù", "ǔ", "û", "ü"),
        # Ф / F
        ("ф", "f", "ph", "φ", "ƒ"),
        # Х / X / H
        ("х", "x", "h", "}{", "×", "χ", "ħ"),
        # Ц
        ("ц", "c", "ts", "tz", "cz", "¢z"),
        # Ч
        ("ч", "ch", "4", "č", "ĉ"),
        # Ш / Щ
        ("ш", "sh", "ŝh", "щ", "Ш"),
        ("щ", "shch", "sch", "sht"),
        # Ь / Ъ
        ("ь", "'", "`", "Ь"),
        ("ъ", '"', "`", "Ъ"),
        # Ы / Ї / Ю / Я / Ў
        ("ы", "yi", "bi", "ɨ"),
        ("ю", "yu", "ju", "io", "∞"),
        ("я", "ya", "9", "ʁ", "ʎ"),
        ("ў", "u", "y", "ў̆"),
        # L / 1 / |
        ("l", "1", "|", "ł", "ĺ", "ļ"),
        # S / 5
        ("s", "5", "ś", "š", "ŝ"),
        # Q / КЮ
        ("q", "ԛ", "ɋ", "Ɋ"),
        # R
        ("r", "г", "ʀ", "ɹ", "ʁ"),
    ]

    WORD_VARIATIONS: Dict[str, List[str]] = {}
    _pattern_cache: Dict[str, re.Pattern[str]] = {}

    LETTER_PATTERNS: Dict[str, Set[str]] = {}
    LETTER_PATTERNS_CASE_SENSITIVE: Dict[str, Set[str]] = {}

    @classmethod
    def _init_patterns(cls) -> None:
        if cls.LETTER_PATTERNS:
            return

        base_map: Dict[str, Set[str]] = {}
        for group in cls.LETTER_GROUPS:
            escaped_variants = {cls._escape_variant(symbol) for symbol in group if symbol}
            for symbol in group:
                if not symbol:
                    continue
                key = symbol.lower()
                base_map.setdefault(key, set()).update(escaped_variants)

        cls.LETTER_PATTERNS = base_map
        cls.LETTER_PATTERNS_CASE_SENSITIVE = base_map.copy()

    @staticmethod
    def _escape_variant(symbol: str) -> str:
        if len(symbol) == 1 and symbol.isalnum():
            return re.escape(symbol)
        return re.escape(symbol)

    @classmethod
    def normalize_text(cls, text: str) -> str:
        text = ZERO_WIDTH_PATTERN.sub("", text)
        text = COMBINING_MARK_PATTERN.sub("", text)
        text = cls._strip_combining(unicodedata.normalize("NFKD", text))
        text = text.lower()
        return text

    @staticmethod
    def _strip_combining(text: str) -> str:
        return "".join(ch for ch in text if unicodedata.category(ch) != "Mn")

    @classmethod
    def add_word_variations(cls, base_word: str, variations: Iterable[str]) -> None:
        cls.WORD_VARIATIONS[base_word.lower()] = [v.lower() for v in variations]

    @classmethod
    def add_letter_pattern(cls, letter: str, variants: Iterable[str]) -> None:
        cls._init_patterns()
        escaped = {cls._escape_variant(ch) for ch in variants}
        cls.LETTER_PATTERNS.setdefault(letter.lower(), set()).update(escaped)

    @classmethod
    def create_pattern(cls, word: str, allow_gaps: bool = False) -> re.Pattern[str]:
        cls._init_patterns()
        key = f"{word.lower()}|gaps={allow_gaps}"
        if key in cls._pattern_cache:
            return cls._pattern_cache[key]

        parts: List[str] = []
        for char in word.lower():
            variants = cls.LETTER_PATTERNS.get(char, {re.escape(char)})
            if len(variants) == 1:
                variant = next(iter(variants))
                if len(variant) == 2 and variant.startswith("\\") and len(char) == 1:
                    parts.append(f"[{variant}]")
                elif len(variant) == 2 and variant.startswith("\\"):
                    parts.append(f"[{variant[-1]}]")
                elif len(variant) == 1:
                    parts.append(f"[{variant}]")
                else:
                    parts.append(f"(?:{variant})")
            else:
                joined = "|".join(sorted(variants, key=len, reverse=True))
                parts.append(f"(?:{joined})")

        if allow_gaps:
            pattern_str = r"\b" + r".*?".join(parts) + r"\b"
        else:
            pattern_str = r"\b" + "".join(parts) + r"\b"

        compiled = re.compile(pattern_str, re.IGNORECASE)
        cls._pattern_cache[key] = compiled
        return compiled

    @classmethod
    def check_word(cls, text: str, word: str) -> bool:
        normalized = cls.normalize_text(text)
        pattern = cls.create_pattern(word)
        if pattern.search(normalized):
            return True

        variations = cls.WORD_VARIATIONS.get(word.lower(), [])
        return any(cls.create_pattern(var).search(normalized) for var in variations)

    @classmethod
    def check_custom_word(cls, text: str, word: str) -> bool:
        normalized = cls.normalize_text(text)
        pattern = cls.create_pattern(word, allow_gaps=True)
        return pattern.search(normalized) is not None

    @classmethod
    def find_matches(cls, text: str, words: Sequence[str]) -> List[str]:
        normalized = cls.normalize_text(text)
        matches: List[str] = []
        for word in words:
            if cls.check_word(normalized, word):
                matches.append(word)
        return matches

PatternChecker._init_patterns()

