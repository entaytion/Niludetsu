import aiohttp
import yaml
from typing import Optional, Dict
from datetime import datetime

class WeatherAPI:
    def __init__(self):
        with open('config/config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            self.api_key = config['apis']['weather']['key']
        
        self.base_url = "http://api.openweathermap.org/data/2.5/weather"
        self.forecast_url = "http://api.openweathermap.org/data/2.5/forecast"
        
        self.weather_icons = {
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
        
        self.city_names = {
            'киев': 'Kyiv', 'київ': 'Kyiv',
            'москва': 'Moscow',
            'харьков': 'Kharkiv', 'харків': 'Kharkiv',
            'одесса': 'Odesa', 'одеса': 'Odesa',
            'львов': 'Lviv', 'львів': 'Lviv',
            'днепр': 'Dnipro', 'дніпро': 'Dnipro',
            'запорожье': 'Zaporizhzhia', 'запоріжжя': 'Zaporizhzhia',
            'хмельницкий': 'Khmelnytskyi', 'хмельницький': 'Khmelnytskyi',
            'винница': 'Vinnytsia', 'вінниця': 'Vinnytsia',
            'житомир': 'Zhytomyr',
            'черкассы': 'Cherkasy', 'черкаси': 'Cherkasy',
            'чернигов': 'Chernihiv', 'чернігів': 'Chernihiv',
            'херсон': 'Kherson',
            'николаев': 'Mykolaiv', 'миколаїв': 'Mykolaiv',
            'полтава': 'Poltava',
            'сумы': 'Sumy', 'суми': 'Sumy',
            'ровно': 'Rivne', 'рівне': 'Rivne',
            'луцк': 'Lutsk', 'луцьк': 'Lutsk',
            'ужгород': 'Uzhhorod',
            'ивано-франковск': 'Ivano-Frankivsk', 'івано-франківськ': 'Ivano-Frankivsk',
            'тернополь': 'Ternopil', 'тернопіль': 'Ternopil',
            'черновцы': 'Chernivtsi', 'чернівці': 'Chernivtsi',
            'мариуполь': 'Mariupol', 'маріуполь': 'Mariupol',
            'кривой рог': 'Kryvyi Rih', 'кривий ріг': 'Kryvyi Rih'
        }

    @staticmethod
    def kelvin_to_celsius(kelvin: float) -> float:
        """Конвертация температуры из Кельвинов в Цельсии"""
        return round(kelvin - 273.15, 1)

    @staticmethod
    def format_time(timestamp: int) -> str:
        """Форматирование временной метки в читаемый формат"""
        return datetime.fromtimestamp(timestamp).strftime('%H:%M')

    def get_weather_icon(self, icon_code: str) -> str:
        """Получение эмодзи иконки погоды по коду"""
        return self.weather_icons.get(icon_code, "❓")

    def get_city_name(self, city: str) -> str:
        """Получение стандартизированного названия города"""
        return self.city_names.get(city.lower(), city)

    async def get_weather(self, city: str) -> Optional[Dict]:
        """Получение текущей погоды для города"""
        city_name = self.get_city_name(city)
        params = {
            'q': city_name,
            'appid': self.api_key,
            'lang': 'ru'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                return None

    def format_weather_data(self, data: Dict) -> Dict:
        """Форматирование данных о погоде в удобный формат"""
        temp = self.kelvin_to_celsius(data['main']['temp'])
        feels_like = self.kelvin_to_celsius(data['main']['feels_like'])
        humidity = data['main']['humidity']
        wind_speed = data['wind']['speed']
        pressure = round(data['main']['pressure'] * 0.750062, 1)  # Конвертация в мм рт.ст.
        visibility = data.get('visibility', 0) // 1000  # Конвертация в км
        description = data['weather'][0]['description']
        icon = self.get_weather_icon(data['weather'][0]['icon'])
        sunrise = self.format_time(data['sys']['sunrise'])
        sunset = self.format_time(data['sys']['sunset'])

        return {
            'temp': temp,
            'feels_like': feels_like,
            'humidity': humidity,
            'wind_speed': wind_speed,
            'pressure': pressure,
            'visibility': visibility,
            'description': description,
            'icon': icon,
            'sunrise': sunrise,
            'sunset': sunset,
            'city_name': data['name']
        } 