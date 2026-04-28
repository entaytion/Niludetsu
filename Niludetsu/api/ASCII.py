from ..tools.Embed import Embed
"""
Модуль для генерации ASCII арта из текста
Использует библиотеку pyfiglet
"""

from pyfiglet import Figlet
from typing import Optional

class ASCIIAPI:
    """Класс для генерации ASCII арта"""

    def __init__(self):
        # Популярные шрифты для ASCII
        self.fonts = {
            'standard': 'standard',
            'banner': 'banner',
            'big': 'big',
            'block': 'block',
            'bubble': 'bubble',
            'digital': 'digital',
            'graffiti': 'graffiti',
            'ivrit': 'ivrit',
            'lean': 'lean',
            'mini': 'mini',
            'script': 'script',
            'shadow': 'shadow',
            'slant': 'slant',
            'small': 'small',
            'smscript': 'smscript',
            'smshadow': 'smshadow',
            'smslant': 'smslant',
            'speed': 'speed',
            'starwars': 'starwars'
        }

    def _generate_ascii(self, text: str, font: str = 'standard') -> Optional[str]:
        """Генерирует ASCII арт из текста"""
        try:
            figlet = Figlet(font=font)
            ascii_art = figlet.renderText(text)
            return ascii_art
        except Exception:
            return None

    def _create_ascii_embed(self, text: str, ascii_art: str, font: str) -> Embed:
        """Создает embed с ASCII артом"""

        # Обрезаем если слишком длинный (Discord лимит)
        if len(ascii_art) > 1900:
            ascii_art = ascii_art[:1900] + "\n..."

        embed = Embed(
            title="🎨 ASCII Art",
            description=f"Исходный текст: `{text}`\nШрифт: **{font}**"
        )

        # ASCII арт в code block
        embed.add_field(
            name="Результат:",
            value=f"```\n{ascii_art}```",
            inline=False
        )

        # Список доступных шрифтов
        fonts_list = ", ".join([f"`{f}`" for f in list(self.fonts.keys())[:10]])
        embed.set_footer(text=f"💡 Доступные шрифты: {fonts_list}")

        return embed

    async def generate_ascii_art(self, ctx, text: str, font: Optional[str] = None):
        """
        Генерирует ASCII арт из текста

        Parameters
        ----------
        ctx : Union[discord.Interaction, commands.Context]
            Контекст команды
        text : str
            Текст для преобразования в ASCII
        font : Optional[str]
            Шрифт для использования (по умолчанию 'standard')
        """
        if not text:
            await ctx.reply(embed=Embed.error(description="Укажите текст для создания ASCII арта!"))
            return

        # Ограничение на длину текста
        if len(text) > 20:
            await ctx.reply(embed=Embed.error(
                description="Текст слишком длинный! Максимум 20 символов.\n💡 ASCII арт лучше смотрится с коротким текстом"
            ))
            return

        # Проверка шрифта
        font = font.lower() if font else 'standard'
        if font not in self.fonts:
            available_fonts = ", ".join([f"`{f}`" for f in list(self.fonts.keys())[:10]])
            await ctx.reply(embed=Embed.error(
                description=f"Неизвестный шрифт!\n\n**Доступные шрифты:**\n{available_fonts}"
            ))
            return

        # Индикатор загрузки
        loading_embed = Embed.default(
            title="🎨 Генерация...",
            description=f"Создаю ASCII арт для текста: `{text}`",
        )
        message = await ctx.reply(embed=loading_embed)

        try:
            ascii_art = self._generate_ascii(text, font)

            if not ascii_art:
                error_embed = Embed.error(description="Не удалось создать ASCII арт.\n💡 Попробуйте другой текст или шрифт")
                return await message.edit(embed=error_embed)

            embed = self._create_ascii_embed(text, ascii_art, font)
            await message.edit(embed=embed)

        except Exception:
            error_embed = Embed.error(description="Произошла ошибка при создании ASCII арта. Попробуйте позже.")
            await message.edit(embed=error_embed)

# Глобальный экземпляр
ascii_api = ASCIIAPI()

