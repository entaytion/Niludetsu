from ..tools.Embed import Embed
"""
Модуль для транслитерации текста между кириллицей и латиницей,
а также для исправления текста, набранного в неправильной раскладке клавиатуры.
"""

from typing import Dict, Tuple

class TransliterationAPI:

    def __init__(self):
        self.LAT_TO_CYR = {
            'a': 'а', 'b': 'б', 'v': 'в', 'g': 'г', 'd': 'д', 'e': 'е',
            'yo': 'ё', 'zh': 'ж', 'z': 'з', 'i': 'и', 'j': 'й', 'k': 'к',
            'l': 'л', 'm': 'м', 'n': 'н', 'o': 'о', 'p': 'п', 'r': 'р',
            's': 'с', 't': 'т', 'u': 'у', 'f': 'ф', 'h': 'х', 'ts': 'ц',
            'ch': 'ч', 'sh': 'ш', 'sch': 'щ', 'y': 'ы', 'yu': 'ю',
            'ya': 'я', "'": 'ь', '#': 'ъ',
            'yi': 'ї', 'ye': 'є', 'ih': 'і', 'g\'': 'ґ',
            'A': 'А', 'B': 'Б', 'V': 'В', 'G': 'Г', 'D': 'Д', 'E': 'Е',
            'Yo': 'Ё', 'Zh': 'Ж', 'Z': 'З', 'I': 'И', 'J': 'Й', 'K': 'К',
            'L': 'Л', 'M': 'М', 'N': 'Н', 'O': 'О', 'P': 'П', 'R': 'Р',
            'S': 'С', 'T': 'Т', 'U': 'У', 'F': 'Ф', 'H': 'Х', 'Ts': 'Ц',
            'Ch': 'Ч', 'Sh': 'Ш', 'Sch': 'Щ', 'Y': 'Ы', 'Yu': 'Ю',
            'Ya': 'Я',
            'Yi': 'Ї', 'Ye': 'Є', 'Ih': 'І', 'G\'': 'Ґ'
        }

        self.CYR_TO_LAT = {}
        for lat, cyr in self.LAT_TO_CYR.items():
            if len(lat) == 1:
                self.CYR_TO_LAT[cyr] = lat

        self.CYR_MULTI = {
            'щ': 'sch', 'ж': 'zh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'ю': 'yu',
            'я': 'ya', 'ё': 'yo', 'ї': 'yi', 'є': 'ye', 'і': 'ih', 'ґ': 'g\'',
            'Щ': 'Sch', 'Ж': 'Zh', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Ю': 'Yu',
            'Я': 'Ya', 'Ё': 'Yo', 'Ї': 'Yi', 'Є': 'Ye', 'І': 'Ih', 'Ґ': 'G\''
        }

        self.LAYOUT_DICT = {
            'q': 'й', 'w': 'ц', 'e': 'у', 'r': 'к', 't': 'е', 'y': 'н',
            'u': 'г', 'i': 'ш', 'o': 'щ', 'p': 'з', '[': 'х', ']': 'ъ',
            'a': 'ф', 's': 'ы', 'd': 'в', 'f': 'а', 'g': 'п', 'h': 'р',
            'j': 'о', 'k': 'л', 'l': 'д', ';': 'ж', "'": 'э', '`': 'ё',
            'z': 'я', 'x': 'ч', 'c': 'с', 'v': 'м', 'b': 'и', 'n': 'т',
            'm': 'ь', ',': 'б', '.': 'ю', '/': '.',
            'Q': 'Й', 'W': 'Ц', 'E': 'У', 'R': 'К', 'T': 'Е', 'Y': 'Н',
            'U': 'Г', 'I': 'Ш', 'O': 'Щ', 'P': 'З', '{': 'Х', '}': 'Ъ',
            'A': 'Ф', 'S': 'Ы', 'D': 'В', 'F': 'А', 'G': 'П', 'H': 'Р',
            'J': 'О', 'K': 'Л', 'L': 'Д', ':': 'Ж', '"': 'Э', '~': 'Ё',
            'Z': 'Я', 'X': 'Ч', 'C': 'С', 'V': 'М', 'B': 'И', 'N': 'Т',
            'M': 'Ь', '<': 'Б', '>': 'Ю', '?': ',',
            '1': '1', '2': '2', '3': '3', '4': '4', '5': '5',
            '6': '6', '7': '7', '8': '8', '9': '9', '0': '0',
            '!': '!', '@': '"', '#': '№', '$': ';', '%': '%',
            '^': ':', '&': '?', '*': '*', '(': '(', ')': ')',
            '-': '-', '_': '_', '=': '=', '+': '+',
            '\\': '\\', '|': '/', ' ': ' '
        }

        self.REVERSE_LAYOUT_DICT = {v: k for k, v in self.LAYOUT_DICT.items()}

        self.icons = {
            'transliteration': '🔄',
            'keyboard_fix': '⌨️',
            'auto_detect': '🔍',
            'cyrillic': '🇷🇺',
            'latin': '🇺🇸'
        }

    def is_cyrillic(self, text: str) -> bool:
        cyr_count = 0
        lat_count = 0

        for char in text:
            if '\u0400' <= char <= '\u04FF':
                cyr_count += 1
            elif ('a' <= char <= 'z') or ('A' <= char <= 'Z'):
                lat_count += 1

        return cyr_count > lat_count

    def detect_text_type(self, text: str) -> Dict[str, any]:
        stats = {
            'cyrillic': 0,
            'latin': 0,
            'digits': 0,
            'symbols': 0,
            'spaces': 0,
            'total': len(text)
        }

        for char in text:
            if '\u0400' <= char <= '\u04FF':
                stats['cyrillic'] += 1
            elif ('a' <= char <= 'z') or ('A' <= char <= 'Z'):
                stats['latin'] += 1
            elif char.isdigit():
                stats['digits'] += 1
            elif char.isspace():
                stats['spaces'] += 1
            else:
                stats['symbols'] += 1

        if stats['cyrillic'] > stats['latin']:
            primary_type = 'cyrillic'
        elif stats['latin'] > stats['cyrillic']:
            primary_type = 'latin'
        else:
            primary_type = 'mixed'

        stats['primary_type'] = primary_type
        return stats

    def lat_to_cyr_convert(self, text: str) -> str:
        result = ''
        i = 0
        while i < len(text):
            if i + 2 < len(text) and text[i:i+3].lower() == 'sch':
                result += 'Щ' if text[i].isupper() else 'щ'
                i += 3
                continue

            if i + 1 < len(text):
                combo = text[i:i+2]
                combo_lower = combo.lower()
                if combo_lower in ['yo', 'zh', 'ts', 'ch', 'sh', 'yu', 'ya', 'yi', 'ye', 'ih', "g'"]:
                    if combo.isupper():
                        result += self.LAT_TO_CYR[combo_lower].upper()
                    else:
                        result += self.LAT_TO_CYR[combo_lower]
                    i += 2
                    continue

            char = text[i]
            char_lower = char.lower()
            if char_lower in self.LAT_TO_CYR:
                if char.isupper():
                    result += self.LAT_TO_CYR[char_lower].upper()
                else:
                    result += self.LAT_TO_CYR[char_lower]
            else:
                result += char
            i += 1

        return result

    def cyr_to_lat_convert(self, text: str) -> str:
        result = ''
        i = 0
        while i < len(text):
            char = text[i]

            if char in self.CYR_MULTI:
                result += self.CYR_MULTI[char]
                i += 1
                continue

            if char in self.CYR_TO_LAT:
                result += self.CYR_TO_LAT[char]
            else:
                result += char
            i += 1

        return result

    def transliterate(self, text: str) -> Tuple[str, str]:
        if self.is_cyrillic(text):
            return self.cyr_to_lat_convert(text), "cyr_to_lat"
        else:
            return self.lat_to_cyr_convert(text), "lat_to_cyr"

    def fix_layout(self, text: str) -> Tuple[str, str]:
        en_to_ru = ''
        ru_to_en = ''

        for char in text:
            if char in self.LAYOUT_DICT:
                en_to_ru += self.LAYOUT_DICT[char]
            else:
                en_to_ru += char

            if char in self.REVERSE_LAYOUT_DICT:
                ru_to_en += self.REVERSE_LAYOUT_DICT[char]
            else:
                ru_to_en += char

        if self.is_cyrillic(text):
            return ru_to_en, "ru_to_en"
        else:
            return en_to_ru, "en_to_ru"

    def create_transliteration_embed(self, original: str, result: str, direction: str, stats: Dict) -> Embed:
        direction_names = {
            'cyr_to_lat': f"{self.icons['cyrillic']} Кириллица → {self.icons['latin']} Латиница",
            'lat_to_cyr': f"{self.icons['latin']} Латиница → {self.icons['cyrillic']} Кириллица"
        }

        embed = Embed(
            title=f"{self.icons['transliteration']} Транслитерация",
            description=direction_names.get(direction, "Автоопределение"),
            color=0x3498DB
        )

        max_length = 1000
        original_display = original[:max_length] + ('...' if len(original) > max_length else '')
        result_display = result[:max_length] + ('...' if len(result) > max_length else '')

        embed.add_field(
            name="📝 Исходный текст:",
            value=f"```{original_display}```",
            inline=False
        )

        embed.add_field(
            name="✨ Результат:",
            value=f"```{result_display}```",
            inline=False
        )

        if stats['total'] > 0:
            cyr_percent = round((stats['cyrillic'] / stats['total']) * 100, 1)
            lat_percent = round((stats['latin'] / stats['total']) * 100, 1)

            embed.add_field(
                name="📊 Анализ текста:",
                value=f"🇷🇺 Кириллица: **{stats['cyrillic']}** ({cyr_percent}%)\n"
                      f"🇺🇸 Латиница: **{stats['latin']}** ({lat_percent}%)\n"
                      f"📏 Всего символов: **{stats['total']}**",
                inline=True
            )

        return embed

    def create_keyboard_fix_embed(self, original: str, result: str, direction: str) -> Embed:
        direction_names = {
            'en_to_ru': f"🇺🇸 EN → 🇷🇺 RU",
            'ru_to_en': f"🇷🇺 RU → 🇺🇸 EN"
        }

        embed = Embed(
            title=f"{self.icons['keyboard_fix']} Исправление раскладки",
            description=direction_names.get(direction, "Автоопределение"),
            color=0xE74C3C
        )

        max_length = 1000
        original_display = original[:max_length] + ('...' if len(original) > max_length else '')
        result_display = result[:max_length] + ('...' if len(result) > max_length else '')

        embed.add_field(
            name="⌨️ Неправильная раскладка:",
            value=f"```{original_display}```",
            inline=False
        )

        embed.add_field(
            name="✅ Исправленный текст:",
            value=f"```{result_display}```",
            inline=False
        )

        embed.add_field(
            name="💡 Совет:",
            value="Используйте Ctrl+Shift или Alt+Shift для смены раскладки",
            inline=False
        )

        return embed

    async def translit_text(self, ctx, text: str = None):
        if text is None:
            if ctx.message.reference and ctx.message.reference.resolved:
                text = ctx.message.reference.resolved.content
                if not text.strip():
                    await ctx.reply(embed=Embed.error(description="Сообщение не содержит текста!"))
                    return
            else:
                await ctx.reply(embed=Embed.error(description="Укажите текст для транслитерации!"))
                return

        if len(text) > 4000:
            await ctx.reply(embed=Embed.error(description="Текст слишком длинный! Максимум 4000 символов."))
            return

        if not text.strip():
            await ctx.reply(embed=Embed.error(description="Текст не может быть пустым!"))
            return

        stats = self.detect_text_type(text)

        result, direction = self.transliterate(text)

        embed = self.create_transliteration_embed(text, result, direction, stats)
        await ctx.reply(embed=embed)

    async def fix_keyboard_layout(self, ctx, text: str = None):
        if text is None:
            if ctx.message.reference and ctx.message.reference.resolved:
                text = ctx.message.reference.resolved.content
                if not text.strip():
                    await ctx.reply(embed=Embed.error(description="Сообщение не содержит текста!"))
                    return
            else:
                await ctx.reply(embed=Embed.error(description="Укажите текст для исправления раскладки!"))
                return

        if len(text) > 4000:
            await ctx.reply(embed=Embed.error(description="Текст слишком длинный! Максимум 4000 символов."))
            return

        if not text.strip():
            await ctx.reply(embed=Embed.error(description="Текст не может быть пустым!"))
            return

        result, direction = self.fix_layout(text)

        if result == text:
            embed = Embed(
                title=f"{self.icons['keyboard_fix']} Раскладка уже корректна",
                description="Текст не нуждается в исправлении раскладки",
                color=0x2ECC71
            )
            embed.add_field(
                name="Текст:",
                value=f"```{text[:1000]}```",
                inline=False
            )
            await ctx.reply(embed=embed)
            return

        embed = self.create_keyboard_fix_embed(text, result, direction)
        await ctx.reply(embed=embed)

transliteration_api = TransliterationAPI()

