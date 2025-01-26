import discord
from discord.ext import commands
from discord import app_commands
from utils import create_embed
from deep_translator import GoogleTranslator
import yaml

# Загружаем конфиг
with open('config/config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

DETECT_LANG_API_KEY = config.get('apis').get('language_detection').get('key')

LANGUAGES = {
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

class Translate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="translate", description="Перевести текст на другой язык")
    @app_commands.describe(
        text="Текст для перевода",
        to_lang="Язык, на который нужно перевести",
        from_lang="Язык оригинала (необязательно, автоопределение)"
    )
    @app_commands.choices(
        to_lang=[
            app_commands.Choice(name=name, value=code)
            for code, name in LANGUAGES.items()
        ],
        from_lang=[
            app_commands.Choice(name=name, value=code)
            for code, name in LANGUAGES.items()
        ]
    )
    async def translate(
        self,
        interaction: discord.Interaction,
        text: str,
        to_lang: str,
        from_lang: str = None
    ):
        await interaction.response.defer()

        try:
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
                    from_lang = detected_lang if detected_lang in LANGUAGES else 'auto'
                except:
                    from_lang = 'auto'

            # Создаем эмбед с переводом
            embed = create_embed(
                title="🌐 Перевод",
                description=(
                    f"**Оригинал ({LANGUAGES.get(from_lang, from_lang)}):**\n{text}\n\n"
                    f"**Перевод ({LANGUAGES.get(to_lang, to_lang)}):**\n{translation}"
                )
            )

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(
                embed=create_embed(
                    description=f"Ошибка при переводе: {str(e)}"
                )
            )

async def setup(bot):
    await bot.add_cog(Translate(bot))