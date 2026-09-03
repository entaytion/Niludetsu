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

    def __init__(self):
        self.api_key = os.getenv('SCREENSHOT_MACHINE_API_KEY')
        self.base_url = "https://api.screenshotmachine.com"
        self.dimension = "1024x768"

    def _validate_url(self, url: str) -> tuple[bool, str]:
        if not url:
            return False, ""

        url = url.strip()

        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        url_pattern = re.compile(
            r'^https?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        if not url_pattern.match(url):
            return False, ""

        return True, url

    async def capture_screenshot(self, url: str) -> Optional[bytes]:
        is_valid, normalized_url = self._validate_url(url)

        if not is_valid:
            return None

        params = {
            'key': self.api_key,
            'url': normalized_url,
            'dimension': self.dimension,
            'device': 'desktop',
            'cacheLimit': '0',
            'delay': '200',
            'zoom': '100'
        }

        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        content_type = response.headers.get('Content-Type', '')

                        if 'image' in content_type:
                            data = await response.read()
                            return data
                        else:
                            error_text = await response.text()
                            return None
                    else:
                        error_text = await response.text()
            return None
        except Exception as e:
            return None

    async def screenshot_command(self, ctx, url: str):
        t = _(ctx=ctx)
        
        if not url:
            error_embed = Embed.error(
                title=t("api_screenshot", "missing_params_title"),
                description=t("api_screenshot", "missing_params_desc"),
            )
            return await ctx.reply(embed=error_embed)

        is_valid, normalized_url = self._validate_url(url)

        if not is_valid:
            error_embed = Embed.error(
                description=t("api_screenshot", "invalid_url_desc", url=url),
            )
            return await ctx.reply(embed=error_embed)

        loading_embed = Embed.default(
            title=t("api_screenshot", "loading_title"),
            description=t("api_screenshot", "loading_desc", url=normalized_url),
        )
        message = await ctx.reply(embed=loading_embed)

        try:
            screenshot_bytes = await self.capture_screenshot(normalized_url)

            if not screenshot_bytes:
                error_embed = Embed.error(
                    description=t("api_screenshot", "fetch_error_desc", url=normalized_url),
                )
                return await message.edit(embed=error_embed)

            image_io = BytesIO(screenshot_bytes)
            file = discord.File(
                fp=image_io,
                filename=f"screenshot_{normalized_url.replace('://', '_').replace('/', '_')[:50]}.jpg"
            )

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

screenshot_api = ScreenshotAPI()

