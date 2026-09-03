from ..locale import _
from ..tools.Embed import Embed
"""
Модуль для перевода текста на различные языки с помощью TranslateAPI
"""

import discord, os
from deep_translator import GoogleTranslator
from discord.ext import commands
from dotenv import load_dotenv

from typing import Optional, Dict, List, Tuple

class TranslateAPI:
    def __init__(self):
        load_dotenv()
        self.detect_lang_api_key = os.getenv('LANGUAGE_DETECTION_API_KEY')
        if not self.detect_lang_api_key:
            raise ValueError("LANGUAGE_DETECTION_API_KEY не найден в .env файле")

        self.languages = {
            'en': 'Английский',
            'ru': 'Русский',
            'uk': 'Украинский', 
            'es': 'Испанский',
            'fr': 'Французский',
            'de': 'Немецкий',
            'it': 'Итальянский',
            'pl': 'Польский',
            'ja': 'Японский',
            'ko': 'Корейский',
            'zh-CN': 'Китайский'
        }

    def get_language_name(self, lang_code: str) -> str:
        return self.languages.get(lang_code, lang_code)

    def get_available_languages(self) -> List[Tuple[str, str]]:
        return [(code, name) for code, name in self.languages.items()]

    async def get_translation_data(self, text: str, to_lang: str, from_lang: Optional[str] = None) -> Dict:
        translator = GoogleTranslator(
            source='auto' if from_lang is None else from_lang,
            target=to_lang
        )

        translation = translator.translate(text)

        if from_lang is None:
            try:
                detected_lang = translator.detect(text)
                from_lang = detected_lang if detected_lang in self.languages else 'auto'
            except:
                from_lang = 'auto'

        return {
            'original_text': text,
            'translated_text': translation,
            'from_lang': from_lang,
            'to_lang': to_lang
        }

    async def translate_text(self, ctx: commands.Context, text: str = None):
        if text is None:
            if hasattr(ctx, 'message') and ctx.message.reference and ctx.message.reference.resolved:
                text = ctx.message.reference.resolved.content
            else:
                t = _(ctx=ctx)
                await ctx.reply(embed=Embed.error(description=t("api_translate", "specify_text")))
                return

        try:
            to_lang = 'ru'
            from_lang: Optional[str] = None

            result = await self.get_translation_data(text, to_lang, from_lang)
            t = _(ctx=ctx)
            embed = self._format_translation_embed(result, t)
            await ctx.reply(embed=embed)

        except Exception as e:
            t = _(ctx=ctx)
            error_embed = Embed.error(
                title=t("api_translate", "error_title"),
                description=t("api_translate", "error_desc", error=str(e))
            )
            await ctx.reply(embed=error_embed)

    def _format_translation_embed(self, result: Dict, t) -> discord.Embed:
        embed = Embed(
            title=t("api_translate", "title"),
            description=(
                f"**{t('api_translate', 'original')} ({self.get_language_name(result['from_lang'])}):**\n"
                f"{result['original_text']}\n\n"
                f"**{t('api_translate', 'translation')} ({self.get_language_name(result['to_lang'])}):**\n"
                f"{result['translated_text']}"
            )
        )
        return embed

    async def translate_text_old(self, text: str, to_lang: str, from_lang: Optional[str] = None) -> Dict:
        return await self.get_translation_data(text, to_lang, from_lang)

translate_api = TranslateAPI()

