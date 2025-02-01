import aiohttp
import os
from typing import Optional, Dict
from dotenv import load_dotenv

class CurrencyAPI:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv('EXCHANGE_RATE_API_KEY')
        if not self.api_key:
            raise ValueError("EXCHANGE_RATE_API_KEY не найден в .env файле")
        
        self.api_url = f"https://v6.exchangerate-api.com/v6/{self.api_key}/latest/"
        self.currencies = {
            "USD": "🇺🇸 Доллар США",
            "EUR": "🇪🇺 Евро", 
            "UAH": "🇺🇦 Украинская гривна",
            "RUB": "🇷🇺 Российский рубль",
            "BYN": "🇧🇾 Белорусский рубль",
            "KZT": "🇰🇿 Казахстанский тенге",
            "GBP": "🇬🇧 Британский фунт",
            "JPY": "🇯🇵 Японская йена",
            "CNY": "🇨🇳 Китайский юань",
            "KRW": "🇰🇷 Южнокорейская вона",
            "TRY": "🇹🇷 Турецкая лира"
        }

    async def get_exchange_rate(self, base_currency: str) -> Optional[Dict]:
        """Получение курсов валют через API"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.api_url}{base_currency}") as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("result") == "success":
                        return data
                return None

    def get_currency_name(self, currency_code: str) -> str:
        """Получить название валюты по её коду"""
        return self.currencies.get(currency_code.upper(), "Неизвестная валюта")

    def is_supported_currency(self, currency_code: str) -> bool:
        """Проверить, поддерживается ли валюта"""
        return currency_code.upper() in self.currencies 