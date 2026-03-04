"""
Модуль для получения и отображения информации о погоде
Использует OpenWeatherMap API (бесплатный)
"""

import aiohttp, os
from dotenv import load_dotenv
from Niludetsu import Embed
from typing import Optional, Dict, Any

class WeatherAPI:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv('WEATHER_API_KEY')
        if not self.api_key:
            raise ValueError("WEATHER_API_KEY не найден в .env файле")

        self.base_url = "http://api.openweathermap.org/data/2.5/weather"

        # Компактная коллекция иконок погоды
        self.weather_icons = {
            "01d": "☀️", "01n": "🌙", "02d": "🌤️", "02n": "☁️",
            "03d": "☁️", "03n": "☁️", "04d": "☁️", "04n": "☁️",
            "09d": "🌧️", "09n": "🌧️", "10d": "🌦️", "10n": "🌧️",
            "11d": "⛈️", "11n": "⛈️", "13d": "🌨️", "13n": "🌨️",
            "50d": "🌫️", "50n": "🌫️"
        }

        # Флаги стран для красивого отображения
        self.country_flags = {
            'UA': '🇺🇦', 'RU': '🇷🇺', 'US': '🇺🇸', 'GB': '🇬🇧',
            'FR': '🇫🇷', 'DE': '🇩🇪', 'JP': '🇯🇵', 'CN': '🇨🇳',
            'IT': '🇮🇹', 'ES': '🇪🇸', 'CA': '🇨🇦', 'AU': '🇦🇺'
        }

    def get_weather_icon(self, icon_code: str) -> str:
        """Получение эмодзи иконки погоды"""
        return self.weather_icons.get(icon_code, "🌍")

    def get_temperature_color(self, temp: float) -> int:
        """Получение цвета эмбеда в зависимости от температуры"""
        if temp >= 30:    return 0xFF4444  # Красный
        elif temp >= 25:  return 0xFF6B35  # Оранжевый  
        elif temp >= 20:  return 0xFFD700  # Золотой
        elif temp >= 15:  return 0x4CAF50  # Зеленый
        elif temp >= 10:  return 0x2196F3  # Синий
        elif temp >= 0:   return 0x9C27B0  # Фиолетовый
        else:             return 0x607D8B  # Серый

    def get_wind_description(self, speed: float) -> str:
        """Получение описания силы ветра"""
        if speed < 1.6:    return "🍃 Тихий"
        elif speed < 3.4:  return "💨 Легкий"
        elif speed < 5.5:  return "💨 Слабый"
        elif speed < 8.0:  return "🌀 Умеренный"
        elif speed < 10.8: return "🌀 Свежий"
        elif speed < 13.9: return "🌪️ Сильный"
        else:              return "🌪️ Очень сильный"

    async def get_weather(self, city: str) -> Optional[Dict]:
        """Получение текущей погоды для города"""
        params = {
            'q': city,
            'appid': self.api_key,
            'lang': 'ru',
            'units': 'metric'
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    return await response.json() if response.status == 200 else None
        except Exception:
            return None

    def format_weather_data(self, data: Dict) -> Dict:
        """Форматирование данных о погоде"""
        return {
            'temp': round(data['main']['temp'], 1),
            'feels_like': round(data['main']['feels_like'], 1),
            'humidity': data['main']['humidity'],
            'wind_speed': data['wind']['speed'],
            'pressure': round(data['main']['pressure'] * 0.750062, 1),
            'visibility': data.get('visibility', 0) // 1000,
            'description': data['weather'][0]['description'],
            'icon': self.get_weather_icon(data['weather'][0]['icon']),
            'icon_code': data['weather'][0]['icon'],
            'sunrise': data['sys']['sunrise'],
            'sunset': data['sys']['sunset'],
            'city_name': data['name'],
            'country': data['sys']['country']
        }

    def create_weather_embed(self, weather_data: Dict[str, Any]) -> Embed:
        """Создает красивый эмбед с информацией о погоде"""

        # Парсим время
        sunrise_time = weather_data['sunrise'].split(' ')[1][:5] if isinstance(weather_data['sunrise'], str) else "Н/Д"
        sunset_time = weather_data['sunset'].split(' ')[1][:5] if isinstance(weather_data['sunset'], str) else "Н/Д"

        # Цвет и флаг
        color = self.get_temperature_color(weather_data['temp'])
        flag = self.country_flags.get(weather_data.get('country', ''), '🌍')
        wind_desc = self.get_wind_description(weather_data['wind_speed'])

        # Создаем эмбед
        embed = Embed(
            title=f"{flag} Погода в {weather_data['city_name']}",
            description=f"{weather_data['icon']} **{weather_data['description'].capitalize()}**\n## 🌡️ {weather_data['temp']}°C\n*Ощущается как {weather_data['feels_like']}°C*",
            color=color
        )

        # Поля с информацией
        embed.add_field(
            name="🌊 Атмосфера", 
            value=f"💧 **{weather_data['humidity']}%** влажность\n📈 **{weather_data['pressure']}** мм рт.ст.", 
            inline=True
        )

        embed.add_field(
            name="💨 Ветер", 
            value=f"{wind_desc}\n**{weather_data['wind_speed']} м/с**", 
            inline=True
        )

        embed.add_field(
            name="👁️ Видимость", 
            value=f"**{weather_data['visibility']} км**\n{'🌫️ Туман' if weather_data['visibility'] < 5 else '✨ Ясно'}", 
            inline=True
        )

        embed.add_field(
            name="🌅 Световой день", 
            value=f"🌄 **Восход:** {sunrise_time} • 🌆 **Закат:** {sunset_time}", 
            inline=False
        )

        # Thumbnail и footer
        embed.set_thumbnail(url=f"http://openweathermap.org/img/wn/{weather_data['icon_code']}@2x.png")
        embed.set_footer(text="🕐 Обновлено только что • OpenWeatherMap")

        return embed

    async def get_weather_info(self, ctx, city: str):
        """Получает и отображает информацию о погоде"""
        if not city:
            return await ctx.reply(embed=Embed.error(description="Укажите название города!"))

        # Индикатор загрузки
        loading_embed = Embed(title="🔄 Загрузка...", description=f"Получаю погоду в **{city}**", color=0x2196F3)
        message = await ctx.reply(embed=loading_embed)

        try:
            weather_info = await self.get_weather(city)

            if not weather_info:
                error_embed = Embed.error(
                    description=f"Не удалось найти **{city}**\n💡 Попробуйте проверить написание или добавить страну")
                return await message.edit(embed=error_embed)

            formatted_data = self.format_weather_data(weather_info)
            embed = self.create_weather_embed(formatted_data)
            await message.edit(embed=embed)

        except Exception:
            error_embed = Embed.error(description="Попробуйте позже")
            await message.edit(embed=error_embed)

# Глобальный экземпляр
weather_api = WeatherAPI()

