from ..locale import _
from ..tools.Embed import Embed
"""
Модуль для взаимодействия с TheColorAPI
"""

import aiohttp, discord, re
from discord.ext import commands

from typing import Dict, Any, Optional, Union

class ColorAPI:

    def __init__(self):
        self.base_url = "https://www.thecolorapi.com/id"
        self.supported_formats = ["hex", "rgb", "cmyk", "hsl", "hsv"]

    @staticmethod
    def clean_color_code(color: str) -> str:
        hex_pattern = r'^#?([A-Fa-f0-9]{3}|[A-Fa-f0-9]{6})$'

        if re.match(hex_pattern, color):
            return color.lstrip('#')

        rgb_pattern = r'^rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)$'
        if match := re.match(rgb_pattern, color):
            r, g, b = map(int, match.groups())
            return f"{r:02x}{g:02x}{b:02x}"

        parts = re.split(r'[,;\s]+', color.strip())
        if len(parts) == 3 and all(p.isdigit() for p in parts):
            r, g, b = map(int, parts)
            return f"{r:02x}{g:02x}{b:02x}"

        return color

    async def get_color_data(self, color: str) -> Optional[Dict[str, Any]]:
        clean_color = self.clean_color_code(color)

        url = f"{self.base_url}?hex={clean_color}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._convert_api_response(data)
                    error_data = await response.text()
                    print(f"Ошибка TheColorAPI: {response.status}, {error_data}")
                    return None
        except Exception as e:
            print(f"Ошибка при запросе к TheColorAPI: {e}")
            return None

    async def get_color_info(self, ctx: commands.Context, color: str):
        if not color:
            t = _(ctx=ctx)
            await ctx.reply(embed=Embed.error(description=t("api_color", "specify_color")))
            return

        try:
            color_data = await self.get_color_data(color)
            if not color_data:
                t = _(ctx=ctx)
                error_embed = Embed.error(description=t("api_color", "fetch_error"))
                await ctx.reply(embed=error_embed)
                return

            embed = self._format_color_embed(color_data)
            await ctx.reply(embed=embed)

        except Exception:
            t = _(ctx=ctx)
            error_embed = Embed.error(description=t("api_color", "api_error"))
            await ctx.reply(embed=error_embed)

    def _convert_api_response(self, api_data: Dict[str, Any]) -> Dict[str, Any]:
        result = {}

        result["name"] = {"value": api_data.get("name", {}).get("value", "Неизвестный цвет")}

        result["hex"] = api_data.get("hex", {}).get("clean", "")

        rgb_data = api_data.get("rgb", {})
        result["rgb"] = {
            "r": rgb_data.get("r", 0),
            "g": rgb_data.get("g", 0),
            "b": rgb_data.get("b", 0)
        }

        hsl_data = api_data.get("hsl", {})
        result["hsl"] = {
            "h": hsl_data.get("h", 0),
            "s": hsl_data.get("s", 0),
            "l": hsl_data.get("l", 0)
        }

        hsv_data = api_data.get("hsv", {})
        result["hsv"] = {
            "h": hsv_data.get("h", 0),
            "s": hsv_data.get("s", 0),
            "v": hsv_data.get("v", 0)
        }

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
        hex_value = self.format_color_value("hex", color_data.get('hex', ''))
        name = color_data.get('name', {}).get('value', 'Неизвестный цвет')

        rgb = color_data.get('rgb', {})
        r = rgb.get('r', 0)
        g = rgb.get('g', 0)
        b = rgb.get('b', 0)
        discord_color = discord.Color.from_rgb(r, g, b)

        embed = discord.Embed(
            title=f"🎨 {name}",
            color=discord_color
        )

        description = []
        for format_name in self.supported_formats:
            if format_data := color_data.get(format_name):
                formatted_value = self.format_color_value(format_name, format_data)
                description.append(f"**{format_name.upper()}:** `{formatted_value}`\n")

        embed.description = "".join(description)

        hex_clean = color_data.get('hex', '').lstrip('#')
        embed.set_thumbnail(url=f"https://singlecolorimage.com/get/{hex_clean}/150x150")

        return embed

    def format_color_value(self, color_type: str, value: Union[Dict[str, Any], str]) -> str:
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

        return str(value)

color_api = ColorAPI()

