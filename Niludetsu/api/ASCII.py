from ..locale import _
from ..tools.Embed import Embed
"""
Модуль для генерации ASCII арта из текста
Использует библиотеку pyfiglet
"""

from pyfiglet import Figlet
from typing import Optional

class ASCIIAPI:

    def __init__(self):
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
        try:
            figlet = Figlet(font=font)
            ascii_art = figlet.renderText(text)
            return ascii_art
        except Exception:
            return None

    def _create_ascii_embed(self, text: str, ascii_art: str, font: str, t) -> Embed:

        if len(ascii_art) > 1900:
            ascii_art = ascii_art[:1900] + "..."

        embed = Embed(
            title=t("api_ascii", "title"),
            description=f"{t('api_ascii', 'source_text')}: `{text}`\n{t('api_ascii', 'font')}: **{font}**"
        )

        embed.add_field(
            name=t("api_ascii", "result"),
            value=f"```\n{ascii_art}```",
            inline=False
        )

        fonts_list = ", ".join([f"`{f}`" for f in list(self.fonts.keys())[:10]])
        embed.set_footer(text=f"{t('api_ascii', 'footer')}: {fonts_list}")

        return embed

    async def generate_ascii_art(self, ctx, text: str, font: Optional[str] = None):
        t = _(ctx=ctx)
        
        if not text:
            await ctx.reply(embed=Embed.error(description=t("api_ascii", "specify_text")))
            return

        if len(text) > 20:
            await ctx.reply(embed=Embed.error(
                description=t("api_ascii", "text_too_long")
            ))
            return

        font = font.lower() if font else 'standard'
        if font not in self.fonts:
            available_fonts = ", ".join([f"`{f}`" for f in list(self.fonts.keys())[:10]])
            await ctx.reply(embed=Embed.error(
                description=t("api_ascii", "unknown_font", available=available_fonts)
            ))
            return

        loading_embed = Embed.default(
            title=t("api_ascii", "generating"),
            description=t("api_ascii", "creating_art", text=text),
        )
        message = await ctx.reply(embed=loading_embed)

        try:
            ascii_art = self._generate_ascii(text, font)

            if not ascii_art:
                error_embed = Embed.error(description=t("api_ascii", "create_failed"))
                return await message.edit(embed=error_embed)

            embed = self._create_ascii_embed(text, ascii_art, font, t)
            await message.edit(embed=embed)

        except Exception:
            error_embed = Embed.error(description=t("api_ascii", "error"))
            await message.edit(embed=error_embed)

ascii_api = ASCIIAPI()

