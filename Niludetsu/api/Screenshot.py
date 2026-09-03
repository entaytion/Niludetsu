from ..locale import _
from ..tools.Embed import Embed
"""
Модуль для создания скриншотов веб-страниц
Использует screenshotmachine.com API
"""

import aiohttp, discord, os, re
from io import BytesIO

from typing import Optional

class ScreenshotAPI:
    """Класс для создания скриншотов веб-страниц"""

    def __init__(self):
        # Используем screenshotmachine.com API
        self.api_key = os.getenv('SCREENSHOT_MACHINE_API_KEY')
        self.base_url = "https://api.screenshotmachine.com"
        self.dimension = "1024x768"  # Разрешение скриншота

    def _validate_url(self, url: str) -> tuple[bool, str]:
        """
        Проверяет и нормализует URL

        Returns:
            (is_valid, normalized_url)
        """
        if not url:
            return False, ""

        # Удаляем пробелы
        url = url.strip()

        # Добавляем https:// если протокол не указан
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        # Базовая проверка URL
        url_pattern = re.compile(
            r'^https?://'  # http:// или https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        if not url_pattern.match(url):
            return False, ""

        return True, url

    async def capture_screenshot(self, url: str) -> Optional[bytes]:
        """
        Создает скриншот веб-страницы

        Parameters
        ----------
        url : str
            URL страницы для скриншота

        Returns
        -------
        Optional[bytes]
            Изображение в виде байтов или None при ошибке
        """
        is_valid, normalized_url = self._validate_url(url)

        if not is_valid:
            return None

        # Формируем URL для API screenshotmachine.com
        params = {
            'key': self.api_key,
            'url': normalized_url,
            'dimension': self.dimension,
            'device': 'desktop',
            'cacheLimit': '0',  # Всегда свежий скриншот
            'delay': '200',  # Задержка для загрузки JS
            'zoom': '100'
        }

        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        content_type = response.headers.get('Content-Type', '')

                        # Проверяем что получили изображение
                        if 'image' in content_type:
                            data = await response.read()
                            return data
                        else:
                            # Если не изображение, читаем текст ошибки
                            error_text = await response.text()
                            return None
                    else:
                        error_text = await response.text()
            return None
        except Exception as e:
            return None

    async def screenshot_command(self, ctx, url: str):
        """
        Команда для создания скриншота веб-страницы

        Parameters
        ----------
        ctx : Union[discord.Interaction, commands.Context]
            Контекст команды
        url : str
            URL страницы для скриншота
        """
        t = _(ctx=ctx)
        
        if not url:
            error_embed = Embed.error(
                title=t("api_screenshot", "missing_params_title"),
                description=t("api_screenshot", "missing_params_desc"),
            )
            return await ctx.reply(embed=error_embed)

        # Проверяем URL
        is_valid, normalized_url = self._validate_url(url)

        if not is_valid:
            error_embed = Embed.error(
                description=t("api_screenshot", "invalid_url_desc", url=url),
            )
            return await ctx.reply(embed=error_embed)

        # Индикатор загрузки
        loading_embed = Embed.default(
            title=t("api_screenshot", "loading_title"),
            description=t("api_screenshot", "loading_desc", url=normalized_url),
        )
        message = await ctx.reply(embed=loading_embed)

        try:
            # Получаем скриншот
            screenshot_bytes = await self.capture_screenshot(normalized_url)

            if not screenshot_bytes:
                error_embed = Embed.error(
                    description=t("api_screenshot", "fetch_error_desc", url=normalized_url),
                )
                return await message.edit(embed=error_embed)

            # Создаем файл из bytes
            image_io = BytesIO(screenshot_bytes)
            file = discord.File(
                fp=image_io,
                filename=f"screenshot_{normalized_url.replace('://', '_').replace('/', '_')[:50]}.jpg"
            )

            # Создаем embed с результатом
            success_embed = Embed.default(
                title=t("api_screenshot", "success_title"),
                description=t("api_screenshot", "success_desc", url=normalized_url),
            )
            success_embed.set_image(url=f"attachment://{file.filename}")
            success_embed.set_footer(text=t("api_screenshot", "footer"))

            await message.edit(embed=success_embed, attachments=[file])

        except discord.HTTPException:
            error_embed = Embed.error(description=t("api_screenshot", "http_error"))
            await message.edit(embed=error_embed)
        except Exception:
            error_embed = Embed.error(description=t("api_screenshot", "generic_error"))
            await message.edit(embed=error_embed)

# Глобальный экземпляр
screenshot_api = ScreenshotAPI()

