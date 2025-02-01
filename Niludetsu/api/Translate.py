import os
from typing import Optional, Dict, List, Tuple
from deep_translator import GoogleTranslator
from dotenv import load_dotenv

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

    async def translate_text(self, text: str, to_lang: str, from_lang: Optional[str] = None) -> Dict:
        """Перевести текст на указанный язык"""
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