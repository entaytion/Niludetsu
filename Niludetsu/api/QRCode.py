"""
Модуль для взаимодействия с API QR-кодов
"""

import aiohttp, discord, io
from discord.ext import commands
from Niludetsu import Embed, Emojis
from typing import Optional, Dict, Any
from urllib.parse import urlencode

class QRCodeAPI:
    """Класс для работы с API QR-кодов"""

    def __init__(self):
        """Инициализация класса"""
        # Используем API от qrcode.chooyee.co (без API ключа)
        self.base_url = "https://qrcode.chooyee.co/qr"
        # API для декодирования QR-кодов
        self.decode_url = "https://api.qrserver.com/v1/read-qr-code/"

    async def get_qrcode_data(self, 
                             data: str, 
                             size: int = 256, 
                             foreground_color: str = "#000000", 
                             background_color: str = "#FFFFFF",
                             logo_url: Optional[str] = None) -> Optional[bytes]:
        """
        Получает данные QR-кода через API

        Parameters
        ----------
        data : str
            Данные для QR-кода (текст или URL)
        size : int
            Размер QR-кода в пикселях (по умолчанию 256)
        foreground_color : str
            Цвет QR-кода в формате HEX (по умолчанию черный)
        background_color : str
            Цвет фона в формате HEX (по умолчанию белый)
        logo_url : Optional[str]
            URL логотипа для размещения в центре QR-кода

        Returns
        -------
        Optional[bytes]
            Байты изображения QR-кода или None при ошибке
        """
        # Очищаем цвета от символа #
        foreground_color = foreground_color.lstrip('#')
        background_color = background_color.lstrip('#')

        # Формируем параметры запроса
        params = {
            "data": data,
            "width": size,
            "height": size,
            "foregroundcolor": foreground_color,
            "backgroundcolor": background_color
        }

        # Добавляем логотип, если указан
        if logo_url:
            params["logo"] = logo_url

        # Формируем URL с параметрами
        url = f"{self.base_url}?{urlencode(params)}"

        try:
            # Выполняем запрос к API
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        # Возвращаем байты изображения
                        return await response.read()
                    # Если произошла ошибка, выводим сообщение
                    error_data = await response.text()
                    print(f"Ошибка API QR-кода: {response.status}, {error_data}")
                    return None
        except Exception as e:
            print(f"Ошибка при запросе к API QR-кода: {e}")
            return None

    async def get_decode_data(self, image_data: bytes) -> Optional[Dict[str, Any]]:
        """
        Получает данные декодирования QR-кода с помощью API

        Parameters
        ----------
        image_data : bytes
            Байты изображения с QR-кодом

        Returns
        -------
        Optional[Dict[str, Any]]
            Словарь с результатами декодирования или None при ошибке
        """
        try:
            # Выполняем запрос к API для декодирования
            async with aiohttp.ClientSession() as session:
                # Создаем объект FormData для отправки файла
                data = aiohttp.FormData()
                data.add_field('file', image_data, filename='qrcode.png', content_type='image/png')

                async with session.post(self.decode_url, data=data) as response:
                    if response.status == 200:
                        # Получаем JSON с результатом декодирования
                        result = await response.json()

                        # Проверяем наличие данных
                        if result and isinstance(result, list) and len(result) > 0:
                            qr_data = result[0].get('symbol', [{}])[0]

                            # Если QR-код найден
                            if qr_data.get('data'):
                                return {
                                    'success': True,
                                    'text': qr_data.get('data'),
                                    'format': qr_data.get('type')
                                }

                            # Если произошла ошибка
                            if qr_data.get('error'):
                                return {
                                    'success': False,
                                    'error': qr_data.get('error')
                                }

                        return {
                            'success': False,
                            'error': 'Не удалось декодировать QR-код'
                        }

                    # Если произошла ошибка запроса
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
        """
        Генерирует QR-код и отправляет пользователю

        Parameters
        ----------
        ctx : commands.Context
            Контекст команды Discord
        content : str
            Содержимое для QR-кода
        color : str
            Цвет QR-кода
        """
        if not content:
            await ctx.reply(embed=Embed.error(title="Ошибка создания QR-кода", description="Укажите текст или ссылку для QR-кода!"))
            return

        try:
            qr_image_data = await self.get_qrcode_data(
                data=content,
                size=256,
                foreground_color=color,
                background_color="#FFFFFF"
            )

            if not qr_image_data:
                error_embed = Embed.error(title="Ошибка создания QR-кода", description="Сервис временно недоступен. Попробуйте позже.")
                await ctx.reply(embed=error_embed)
                return

            img_byte_arr = io.BytesIO(qr_image_data)
            img_byte_arr.seek(0)

            embed = self._format_qrcode_embed(content)
            file = discord.File(img_byte_arr, filename="qrcode.png")
            embed.set_image(url="attachment://qrcode.png")

            await ctx.reply(embed=embed, file=file)

        except Exception as e:
            error_embed = Embed.error(title="Ошибка создания QR-кода", description=f"Произошла ошибка: {str(e)}")
            await ctx.reply(embed=error_embed)

    async def decode_qrcode(self, ctx: commands.Context, image: discord.Attachment):
        """
        Декодирует QR-код из изображения и отправляет результат пользователю

        Parameters
        ----------
        ctx : commands.Context
            Контекст команды Discord
        image : discord.Attachment
            Изображение с QR-кодом
        """
        if not image:
            await ctx.reply(embed=Embed.error(title="Ошибка декодирования QR-кода", description="Загрузите изображение с QR-кодом!"))
            return

        try:
            if not image.content_type or not image.content_type.startswith('image/'):
                error_embed = Embed.error(title="Неверный формат", description="Пожалуйста, загрузите изображение с QR-кодом")
                await ctx.reply(embed=error_embed)
                return

            img_bytes = await image.read()
            decode_result = await self.get_decode_data(img_bytes)

            if not decode_result or not decode_result.get('success', False):
                error_message = decode_result.get('error', 'Не удалось распознать QR-код') if decode_result else 'Не удалось распознать QR-код'
                error_embed = Embed.error(title="QR-код не распознан", description=error_message)
                await ctx.reply(embed=error_embed)
                return

            embed = self._format_decode_embed(decode_result)
            await ctx.reply(embed=embed)

        except Exception as e:
            error_embed = Embed.error(title="Ошибка декодирования QR-кода", description=f"Произошла ошибка: {str(e)}")
            await ctx.reply(embed=error_embed)

    def _format_qrcode_embed(self, content: str) -> discord.Embed:
        """
        Форматирует эмбед для сгенерированного QR-кода

        Parameters
        ----------
        content : str
            Содержимое QR-кода

        Returns
        -------
        discord.Embed
            Отформатированный эмбед
        """
        is_url = content.startswith(('http://', 'https://', 'www.'))

        embed = Embed(
            title=f"{Emojis.SUCCESS} QR-код создан",
            description=f"{'🔗 **Ссылка:**' if is_url else '📝 **Содержимое:**'} `{content}`"
        )

        return embed

    def _format_decode_embed(self, decode_result: Dict[str, Any]) -> discord.Embed:
        """
        Форматирует эмбед для декодированного QR-кода

        Parameters
        ----------
        decode_result : Dict[str, Any]
            Результат декодирования

        Returns
        -------
        discord.Embed
            Отформатированный эмбед
        """
        qr_data = decode_result.get('text', '')
        qr_format = decode_result.get('format', 'QR-код')
        is_url = qr_data.startswith(('http://', 'https://', 'www.'))

        embed = Embed(
            title=f"{Emojis.SUCCESS} QR-код распознан",
            description=(
                f"🔎 **Формат:** `{qr_format}`"
                f"{'🔗 **Ссылка:**' if is_url else '📝 **Текст:**'} `{qr_data}`"
            )
        )

        return embed

# Создаем экземпляр для импорта
qrcode_api = QRCodeAPI()

