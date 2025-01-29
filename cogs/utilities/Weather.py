import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.utils.embed import create_embed
import aiohttp
import yaml
from datetime import datetime
from transliterate import translit
from Niludetsu.core.base import EMOJIS

# Загрузка конфигурации из файла
with open('config/config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

WEATHER_API_KEY = config.get('apis').get('weather').get('key')

BASE_URL = "http://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "http://api.openweathermap.org/data/2.5/forecast"

CITY_NAMES = {
    'киев': 'Kyiv',
    'київ': 'Kyiv',
    'москва': 'Moscow',
    'харьков': 'Kharkiv',
    'харків': 'Kharkiv',
    'одесса': 'Odesa',
    'одеса': 'Odesa',
    'львов': 'Lviv',
    'львів': 'Lviv',
    'днепр': 'Dnipro',
    'дніпро': 'Dnipro',
    'запорожье': 'Zaporizhzhia',
    'запоріжжя': 'Zaporizhzhia',
    'хмельницкий': 'Khmelnytskyi',
    'хмельницький': 'Khmelnytskyi',
    'винница': 'Vinnytsia',
    'вінниця': 'Vinnytsia',
    'житомир': 'Zhytomyr',
    'черкассы': 'Cherkasy',
    'черкаси': 'Cherkasy',
    'чернигов': 'Chernihiv',
    'чернігів': 'Chernihiv',
    'херсон': 'Kherson',
    'николаев': 'Mykolaiv',
    'миколаїв': 'Mykolaiv',
    'полтава': 'Poltava',
    'сумы': 'Sumy',
    'суми': 'Sumy',
    'ровно': 'Rivne',
    'рівне': 'Rivne',
    'луцк': 'Lutsk',
    'луцьк': 'Lutsk',
    'ужгород': 'Uzhhorod',
    'ивано-франковск': 'Ivano-Frankivsk',
    'івано-франківськ': 'Ivano-Frankivsk',
    'тернополь': 'Ternopil',
    'тернопіль': 'Ternopil',
    'черновцы': 'Chernivtsi',
    'чернівці': 'Chernivtsi',
    'мариуполь': 'Mariupol',
    'маріуполь': 'Mariupol',
    'кривой рог': 'Kryvyi Rih',
    'кривий ріг': 'Kryvyi Rih'
}

WEATHER_ICONS = {
    "01d": "☀️", "01n": "🌙",
    "02d": "🌤️", "02n": "☁️",
    "03d": "☁️", "03n": "☁️",
    "04d": "☁️", "04n": "☁️",
    "09d": "🌧️", "09n": "🌧️",
    "10d": "🌦️", "10n": "🌧️",
    "11d": "⛈️", "11n": "⛈️",
    "13d": "🌨️", "13n": "🌨️",
    "50d": "🌫️", "50n": "🌫️"
}

class Weather(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def kelvin_to_celsius(self, kelvin):
        return round(kelvin - 273.15, 1)

    def format_time(self, timestamp):
        return datetime.fromtimestamp(timestamp).strftime('%H:%M')

    def format_weather_message(self, data):
        temp = self.kelvin_to_celsius(data['main']['temp'])
        feels_like = self.kelvin_to_celsius(data['main']['feels_like'])
        humidity = data['main']['humidity']
        wind_speed = data['wind']['speed']
        pressure = round(data['main']['pressure'] * 0.750062, 1)  # Конвертация в мм рт.ст.
        visibility = data.get('visibility', 0) // 1000  # Конвертация в км
        description = data['weather'][0]['description']
        icon = WEATHER_ICONS.get(data['weather'][0]['icon'], "❓")
        
        sunrise = self.format_time(data['sys']['sunrise'])
        sunset = self.format_time(data['sys']['sunset'])
        
        # Направление ветра
        wind_deg = data.get('wind', {}).get('deg', 0)
        wind_direction = "↑"  # По умолчанию север
        if 22.5 <= wind_deg < 67.5: wind_direction = "↗️"
        elif 67.5 <= wind_deg < 112.5: wind_direction = "→"
        elif 112.5 <= wind_deg < 157.5: wind_direction = "↘️"
        elif 157.5 <= wind_deg < 202.5: wind_direction = "↓"
        elif 202.5 <= wind_deg < 247.5: wind_direction = "↙️"
        elif 247.5 <= wind_deg < 292.5: wind_direction = "←"
        elif 292.5 <= wind_deg < 337.5: wind_direction = "↖️"

        return (
            f"{icon} **{description.capitalize()}**\n\n"
            f"🌡️ Температура: **{temp}°C**\n"
            f"🤔 Ощущается как: **{feels_like}°C**\n"
            f"💧 Влажность: **{humidity}%**\n"
            f"🌪️ Ветер: **{wind_speed} м/с** {wind_direction}\n"
            f"🌡️ Давление: **{pressure} мм рт.ст.**\n"
            f"👁️ Видимость: **{visibility} км**\n"
            f"🌅 Восход: **{sunrise}**\n"
            f"🌇 Закат: **{sunset}**"
        )

    def get_city_name(self, city):
        city_lower = city.lower()
        if city_lower in CITY_NAMES:
            return CITY_NAMES[city_lower]
        try:
            return translit(city, 'uk', reversed=True)
        except:
            return city

    @app_commands.command(name="weather", description="Узнать погоду в указанном городе")
    @app_commands.describe(city="Название города")
    async def weather(self, interaction: discord.Interaction, city: str):
        if not WEATHER_API_KEY:
            await interaction.response.send_message(
                embed=create_embed(
                    description="API-ключ для погоды не настроен!"
                )
            )
            return

        await interaction.response.defer()

        try:
            city_name = self.get_city_name(city)
            async with aiohttp.ClientSession() as session:
                # Получаем текущую погоду
                params = {
                    'q': f"{city_name},UA",
                    'appid': WEATHER_API_KEY,
                    'lang': 'ru'
                }

                async with session.get(BASE_URL, params=params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Ошибка API: {error_text} (код {response.status})")

                    data = await response.json()

                # Получаем прогноз на ближайшие часы
                params['cnt'] = 3  # Количество временных точек
                async with session.get(FORECAST_URL, params=params) as response:
                    if response.status == 200:
                        forecast_data = await response.json()
                        forecast_text = "\n\n📅 **Прогноз на ближайшие часы:**\n"
                        for item in forecast_data['list'][:3]:
                            temp = self.kelvin_to_celsius(item['main']['temp'])
                            time = datetime.fromtimestamp(item['dt']).strftime('%H:%M')
                            icon = WEATHER_ICONS.get(item['weather'][0]['icon'], "❓")
                            forecast_text += f"{time}: {icon} **{temp}°C** ({item['weather'][0]['description']})\n"
                    else:
                        forecast_text = ""

                if not isinstance(data, dict):
                    raise Exception("Получен некорректный формат ответа от API")

                weather_info = self.format_weather_message(data) + forecast_text

                embed = create_embed(
                    title=f"🌍 Погода в {data['name']}",
                    description=weather_info,
                    footer={"text": f"Последнее обновление: {datetime.now().strftime('%H:%M:%S')}"}
                )
                await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(
                embed=create_embed(
                    description=f"Произошла ошибка: {str(e)}"
                )
            )

async def setup(bot):
    await bot.add_cog(Weather(bot))