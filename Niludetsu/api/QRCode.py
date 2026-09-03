from ..locale import _
from ..tools.Embed import Embed
from ..tools.Emojis import Emojis
"""
Модуль для взаимодействия с API QR-кодов
"""

import aiohttp, discord, io
from discord.ext import commands

from typing import Optional, Dict, Any
from urllib.parse import urlencode

class QRCodeAPI:

    def __init__(self):
        self.base_url = "https://qrcode.chooyee.co/qr"
        self.decode_url = "https://api.qrserver.com/v1/read-qr-code/"

    async def get_qrcode_data(self, 
                             data: str, 
                             size: int = 256, 
                             foreground_color: str = "#000000", 
                             background_color: str = "#FFFFFF",
                             logo_url: Optional[str] = None) -> Optional[bytes]:
        foreground_color = foreground_color.lstrip('#')
        background_color = background_color.lstrip('#')

        params = {
            "data": data,
            "width": size,
            "height": size,
            "foregroundcolor": foreground_color,
            "backgroundcolor": background_color
        }

        if logo_url:
            params["logo"] = logo_url

        url = f"{self.base_url}?{urlencode(params)}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.read()
                    error_data = await response.text()
                    print(f"Ошибка API QR-кода: {response.status}, {error_data}")
                    return None
        except Exception as e:
            print(f"Ошибка при запросе к API QR-кода: {e}")
            return None

    async def get_decode_data(self, image_data: bytes) -> Optional[Dict[str, Any]]:
        try:
            async with aiohttp.ClientSession() as session:
                data = aiohttp.FormData()
                data.add_field('file', image_data, filename='qrcode.png', content_type='image/png')

                async with session.post(self.decode_url, data=data) as response:
                    if response.status == 200:
                        result = await response.json()

                        if result and isinstance(result, list) and len(result) > 0:
                            qr_data = result[0].get('symbol', [{}])[0]

                            if qr_data.get('data'):
                                return {
                                    'success': True,
                                    'text': qr_data.get('data'),
                                    'format': qr_data.get('type')
                                }

                            if qr_data.get('error'):
                                return {
                                    'success': False,
                                    'error': qr_data.get('error')
                                }

                        return {
                            'success': False,
                            'error': 'Не удалось декодировать QR-код'
                        }

                    error_data = await response.text()
                    print(f"Ошибка API декодирования QR-кода: {response.status}, {error_data}")
                    return {
                        'success': False,
                        'error': f'Ошибка сервиса декодирования: {response.status}'
                    }
        except Exception as e:
            print(f"Ошибка при запросе к API декодирования QR-кода: {e}")
            return {
                'success': False,
                'error': f'Ошибка запроса: {str(e)}'
            }

    async def generate_qrcode(self, ctx: commands.Context, content: str, color: str = "#000000"):
        t = _(ctx=ctx)
        
        if not content:
            await ctx.reply(embed=Embed.error(title=t("api_qrcode", "create_error_title"), description=t("api_qrcode", "specify_content")))
            return

        try:
            qr_image_data = await self.get_qrcode_data(
                data=content,
                size=256,
                foreground_color=color,
                background_color="#FFFFFF"
            )

            if not qr_image_data:
                error_embed = Embed.error(title=t("api_qrcode", "create_error_title"), description=t("api_qrcode", "service_unavailable"))
                await ctx.reply(embed=error_embed)
                return

            img_byte_arr = io.BytesIO(qr_image_data)
            img_byte_arr.seek(0)

            embed = self._format_qrcode_embed(content, t)
            file = discord.File(img_byte_arr, filename="qrcode.png")
            embed.set_image(url="attachment://qrcode.png")

            await ctx.reply(embed=embed, file=file)

        except Exception as e:
            error_embed = Embed.error(title=t("api_qrcode", "create_error_title"), description=t("api_qrcode", "generic_error", error=str(e)))
            await ctx.reply(embed=error_embed)

    async def decode_qrcode(self, ctx: commands.Context, image: discord.Attachment):
        t = _(ctx=ctx)
        
        if not image:
            await ctx.reply(embed=Embed.error(title=t("api_qrcode", "decode_error_title"), description=t("api_qrcode", "specify_image")))
            return

        try:
            if not image.content_type or not image.content_type.startswith('image/'):
                error_embed = Embed.error(title=t("api_qrcode", "invalid_format"), description=t("api_qrcode", "invalid_format_desc"))
                await ctx.reply(embed=error_embed)
                return

            img_bytes = await image.read()
            decode_result = await self.get_decode_data(img_bytes)

            if not decode_result or not decode_result.get('success', False):
                error_message = decode_result.get('error', t("api_qrcode", "unrecognized")) if decode_result else t("api_qrcode", "unrecognized")
                error_embed = Embed.error(title=t("api_qrcode", "unrecognized_title"), description=error_message)
                await ctx.reply(embed=error_embed)
                return

            embed = self._format_decode_embed(decode_result, t)
            await ctx.reply(embed=embed)

        except Exception as e:
            error_embed = Embed.error(title=t("api_qrcode", "decode_error_title"), description=t("api_qrcode", "generic_error", error=str(e)))
            await ctx.reply(embed=error_embed)

    def _format_qrcode_embed(self, content: str, t) -> discord.Embed:
        is_url = content.startswith(('http://', 'https://', 'www.'))

        embed = Embed(
            title=t("api_qrcode", "created_title", emoji=Emojis.SUCCESS),
            description=f"{t('api_qrcode', 'link_label') if is_url else t('api_qrcode', 'content_label')} `{content}`"
        )

        return embed

    def _format_decode_embed(self, decode_result: Dict[str, Any], t) -> discord.Embed:
        qr_data = decode_result.get('text', '')
        qr_format = decode_result.get('format', t("api_qrcode", "format_default"))
        is_url = qr_data.startswith(('http://', 'https://', 'www.'))

        embed = Embed(
            title=t("api_qrcode", "decoded_title", emoji=Emojis.SUCCESS),
            description=(
                f"{t('api_qrcode', 'format_label')} `{qr_format}`\n"
                f"{t('api_qrcode', 'link_label') if is_url else t('api_qrcode', 'text_label')} `{qr_data}`"
            )
        )

        return embed

qrcode_api = QRCodeAPI()

