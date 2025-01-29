import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.utils.embed import create_embed
from Niludetsu.api.Translate import TranslateAPI

class Translate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.translate_api = TranslateAPI()

    @app_commands.command(name="translate", description="Перевести текст на другой язык")
    @app_commands.describe(
        text="Текст для перевода",
        to_lang="Язык, на который нужно перевести",
        from_lang="Язык оригинала (необязательно, автоопределение)"
    )
    @app_commands.choices(
        to_lang=[
            app_commands.Choice(name=name, value=code)
            for code, name in TranslateAPI().languages.items()
        ],
        from_lang=[
            app_commands.Choice(name=name, value=code)
            for code, name in TranslateAPI().languages.items()
        ]
    )
    async def translate(
        self,
        interaction: discord.Interaction,
        text: str,
        to_lang: str,
        from_lang: str = None
    ):
        """Перевести текст на указанный язык"""
        await interaction.response.defer()

        # Выполняем перевод
        result = await self.translate_api.translate_text(text, to_lang, from_lang)

        # Создаем эмбед с переводом
        embed = create_embed(
            title="🌐 Перевод",
            description=(
                f"**Оригинал ({self.translate_api.get_language_name(result['from_lang'])}):**\n"
                f"{result['original_text']}\n\n"
                f"**Перевод ({self.translate_api.get_language_name(result['to_lang'])}):**\n"
                f"{result['translated_text']}"
            )
        )

        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Translate(bot))