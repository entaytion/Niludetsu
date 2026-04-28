from ..tools.Embed import Embed
"""
Модуль для взаимодействия с TheColorAPI
"""

import aiohttp, discord, re
from discord.ext import commands

from typing import Dict, Any, Optional, Union

class ColorAPI:
    """Класс для взаимодействия с TheColorAPI"""

    def __init__(self):
        """Инициализация класса"""
        self.base_url = "https://www.thecolorapi.com/id"
        # Поддерживаемые форматы цветов для отображения
        self.supported_formats = ["hex", "rgb", "cmyk", "hsl", "hsv"]

    @staticmethod
    def clean_color_code(color: str) -> str:
        """
        Очищает и нормализует код цвета для API

        Parameters
        ----------
        color : str
            Код цвета в любом формате

        Returns
        -------
        str
            Нормализованный HEX-код цвета без #
        """
        # Простой HEX с # или без
        hex_pattern = r'^#?([A-Fa-f0-9]{3}|[A-Fa-f0-9]{6})$'

        # Если это уже HEX
        if re.match(hex_pattern, color):
            return color.lstrip('#')

        # RGB в формате rgb(r,g,b)
        rgb_pattern = r'^rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)$'
        if match := re.match(rgb_pattern, color):
            r, g, b = map(int, match.groups())
            return f"{r:02x}{g:02x}{b:02x}"

        # Пробуем разделить на компоненты (для RGB, CMYK и т.д.)
        parts = re.split(r'[,;\s]+', color.strip())
        if len(parts) == 3 and all(p.isdigit() for p in parts):
            # Похоже на RGB
            r, g, b = map(int, parts)
            return f"{r:02x}{g:02x}{b:02x}"

        # Если не удалось нормализовать, возвращаем как есть
        return color

    async def get_color_data(self, color: str) -> Optional[Dict[str, Any]]:
        """
        Получает информацию о цвете из TheColorAPI

        Parameters
        ----------
        color : str
            Код цвета в любом формате

        Returns
        -------
        Optional[Dict[str, Any]]
            Словарь с информацией о цвете или None при ошибке
        """
        # Очищаем и нормализуем код цвета
        clean_color = self.clean_color_code(color)

        # Формируем URL для запроса
        url = f"{self.base_url}?hex={clean_color}"

        # Выполняем запрос к API
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Преобразуем ответ TheColorAPI в наш формат
                        return self._convert_api_response(data)
                    # Если произошла ошибка
                    error_data = await response.text()
                    print(f"Ошибка TheColorAPI: {response.status}, {error_data}")
                    return None
        except Exception as e:
            print(f"Ошибка при запросе к TheColorAPI: {e}")
            return None

    async def get_color_info(self, ctx: commands.Context, color: str):
        """
        Получает информацию о цвете и отправляет ее пользователю

        Parameters
        ----------
        ctx : commands.Context
            Контекст команды Discord
        color : str
            Код цвета для анализа
        """
        if not color:
            await ctx.reply(embed=Embed.error(description="Укажите цвет!"))
            return

        try:
            color_data = await self.get_color_data(color)
            if not color_data:
                error_embed = Embed.error(description="Не удалось получить информацию о цвете. Проверьте формат и попробуйте снова.")
                await ctx.reply(embed=error_embed)
                return

            embed = self._format_color_embed(color_data)
            await ctx.reply(embed=embed)

        except Exception:
            error_embed = Embed.error(description="Произошла ошибка при получении информации о цвете. Попробуйте позже.")
            await ctx.reply(embed=error_embed)

    def _convert_api_response(self, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Преобразует ответ TheColorAPI в наш формат

        Parameters
        ----------
        api_data : Dict[str, Any]
            Данные от TheColorAPI

        Returns
        -------
        Dict[str, Any]
            Преобразованные данные
        """
        result = {}

        # Название цвета
        result["name"] = {"value": api_data.get("name", {}).get("value", "Неизвестный цвет")}

        # HEX
        result["hex"] = api_data.get("hex", {}).get("clean", "")

        # RGB
        rgb_data = api_data.get("rgb", {})
        result["rgb"] = {
            "r": rgb_data.get("r", 0),
            "g": rgb_data.get("g", 0),
            "b": rgb_data.get("b", 0)
        }

        # HSL
        hsl_data = api_data.get("hsl", {})
        result["hsl"] = {
            "h": hsl_data.get("h", 0),
            "s": hsl_data.get("s", 0),
            "l": hsl_data.get("l", 0)
        }

        # HSV
        hsv_data = api_data.get("hsv", {})
        result["hsv"] = {
            "h": hsv_data.get("h", 0),
            "s": hsv_data.get("s", 0),
            "v": hsv_data.get("v", 0)
        }

        # CMYK (конвертируем из RGB)
        r, g, b = result["rgb"]["r"] / 255, result["rgb"]["g"] / 255, result["rgb"]["b"] / 255
        k = 1 - max(r, g, b)

        if k == 1:
            c, m, y = 0, 0, 0
        else:
            c = (1 - r - k) / (1 - k)
            m = (1 - g - k) / (1 - k)
            y = (1 - b - k) / (1 - k)

        result["cmyk"] = {
            "c": round(c * 100) / 100,
            "m": round(m * 100) / 100,
            "y": round(y * 100) / 100,
            "k": round(k * 100) / 100
        }

        return result

    def _format_color_embed(self, color_data: Dict[str, Any]) -> discord.Embed:
        """
        Форматирует эмбед с информацией о цвете

        Parameters
        ----------
        color_data : Dict[str, Any]
            Данные о цвете от API

        Returns
        -------
        discord.Embed
            Отформатированный эмбед с информацией о цвете
        """
        # Получаем основные данные из ответа API
        hex_value = self.format_color_value("hex", color_data.get('hex', ''))
        name = color_data.get('name', {}).get('value', 'Неизвестный цвет')

        # Получаем RGB для цвета Discord
        rgb = color_data.get('rgb', {})
        r = rgb.get('r', 0)
        g = rgb.get('g', 0)
        b = rgb.get('b', 0)
        discord_color = discord.Color.from_rgb(r, g, b)

        # Создаем эмбед
        embed = discord.Embed(
            title=f"🎨 {name}",
            color=discord_color
        )

        # Формируем описание со всеми поддерживаемыми форматами
        description = []
        for format_name in self.supported_formats:
            if format_data := color_data.get(format_name):
                formatted_value = self.format_color_value(format_name, format_data)
                description.append(f"**{format_name.upper()}:** `{formatted_value}`\n")

        embed.description = "".join(description)

        # Добавляем предпросмотр цвета (чистый HEX без #)
        hex_clean = color_data.get('hex', '').lstrip('#')
        embed.set_thumbnail(url=f"https://singlecolorimage.com/get/{hex_clean}/150x150")

        return embed

    def format_color_value(self, color_type: str, value: Union[Dict[str, Any], str]) -> str:
        """
        Форматирует значение цвета в читаемый вид

        Parameters
        ----------
        color_type : str
            Тип цвета (hex, rgb, cmyk, hsl, hsv)
        value : Union[Dict[str, Any], str]
            Значение цвета

        Returns
        -------
        str
            Отформатированное значение цвета
        """
        if color_type == "hex":
            return f"#{value}" if isinstance(value, str) else "N/A"

        if color_type == "rgb":
            return f"rgb({value.get('r', 0)}, {value.get('g', 0)}, {value.get('b', 0)})"

        if color_type == "cmyk":
            return f"cmyk({value.get('c', 0):.2f}, {value.get('m', 0):.2f}, {value.get('y', 0):.2f}, {value.get('k', 0):.2f})"

        if color_type == "hsl":
            return f"hsl({value.get('h', 0)}°, {value.get('s', 0)}%, {value.get('l', 0)}%)"

        if color_type == "hsv":
            return f"hsv({value.get('h', 0)}°, {value.get('s', 0)}%, {value.get('v', 0)}%)"

        # Для других форматов возвращаем строковое представление словаря
        return str(value)

# Создаем экземпляр для импорта
color_api = ColorAPI()

