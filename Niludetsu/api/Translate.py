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
        """Получить название языка по его коду"""
        return self.languages.get(lang_code, lang_code)

    def get_available_languages(self) -> List[Tuple[str, str]]:
        """Получить список доступных языков в формате (код, название)"""
        return [(code, name) for code, name in self.languages.items()]

    async def get_translation_data(self, text: str, to_lang: str, from_lang: Optional[str] = None) -> Dict:
        """
        Получает данные перевода

        Parameters
        ----------
        text : str
            Текст для перевода
        to_lang : str
            Язык для перевода
        from_lang : Optional[str]
            Исходный язык (если None, то автоопределение)

        Returns
        -------
        Dict
            Данные перевода
        """
        # Создаем переводчик
        translator = GoogleTranslator(
            source='auto' if from_lang is None else from_lang,
            target=to_lang
        )

        # Выполняем перевод
        translation = translator.translate(text)

        # Если язык не указан, определяем его
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
        """
        Переводит текст на русский язык и отправляет пользователю

        Parameters
        ----------
        ctx : commands.Context
            Контекст команды Discord
        text : str, optional
            Текст для перевода
        """
        if text is None:
            if hasattr(ctx, 'message') and ctx.message.reference and ctx.message.reference.resolved:
                text = ctx.message.reference.resolved.content
            else:
                await ctx.reply(embed=Embed.error(description="Укажите текст для перевода или ответьте на сообщение"))
                return

        try:
            # Всегда переводим на русский, исходный язык автоопределяется
            to_lang = 'ru'
            from_lang: Optional[str] = None

            result = await self.get_translation_data(text, to_lang, from_lang)
            embed = self._format_translation_embed(result)
            await ctx.reply(embed=embed)

        except Exception as e:
            error_embed = Embed.error(
                title="Ошибка перевода",
                description=f"Произошла ошибка при переводе: {str(e)}"
            )
            await ctx.reply(embed=error_embed)

    def _format_translation_embed(self, result: Dict) -> discord.Embed:
        """
        Форматирует эмбед с переводом

        Parameters
        ----------
        result : Dict
            Данные перевода

        Returns
        -------
        discord.Embed
            Отформатированный эмбед с переводом
        """
        embed = Embed(
            title="🌐 Перевод",
            description=(
                f"**Оригинал ({self.get_language_name(result['from_lang'])}):**"
                f"{result['original_text']}"
                f"**Перевод ({self.get_language_name(result['to_lang'])}):**"
                f"{result['translated_text']}"
            )
        )
        return embed

    # Оставляем старый метод для обратной совместимости
    async def translate_text_old(self, text: str, to_lang: str, from_lang: Optional[str] = None) -> Dict:
        """Старый метод для обратной совместимости"""
        return await self.get_translation_data(text, to_lang, from_lang)

# Создаем экземпляр для импорта
translate_api = TranslateAPI()

