import discord
from discord.ext import commands
from discord import app_commands
from utils import create_embed
import aiohttp
import json
from datetime import datetime
from transliterate import translit

# Загрузка конфигурации из файла
with open('config/config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

WEATHER_API_KEY = config.get('WEATHER_API_KEY')

BASE_URL = "http://api.openweathermap.org/data/2.5/weather"

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

    def format_weather_message(self, data):
        temp = self.kelvin_to_celsius(data['main']['temp'])
        feels_like = self.kelvin_to_celsius(data['main']['feels_like'])
        humidity = data['main']['humidity']
        wind_speed = data['wind']['speed']
        description = data['weather'][0]['description']
        icon = WEATHER_ICONS.get(data['weather'][0]['icon'], "❓")

        return (
            f"{icon} **{description.capitalize()}**\n\n"
            f"🌡️ Температура: **{temp}°C**\n"
            f"🤔 Ощущается как: **{feels_like}°C**\n"
            f"💧 Влажность: **{humidity}%**\n"
            f"💨 Скорость ветра: **{wind_speed} м/с**"
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

                if not isinstance(data, dict):
                    raise Exception("Получен некорректный формат ответа от API")

                weather_info = self.format_weather_message(data)

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