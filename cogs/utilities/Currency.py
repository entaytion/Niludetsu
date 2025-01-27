import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
from utils import create_embed, EMOJIS
import yaml

class Currency(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Загружаем API ключ из конфигурации
        with open('config/config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            self.api_key = config['apis']['exchange_rate']['key']
            
        self.api_url = f"https://v6.exchangerate-api.com/v6/{self.api_key}/latest/"
        self.currencies = {
            "USD": "🇺🇸 Доллар США",
            "EUR": "🇪🇺 Евро", 
            "UAH": "🇺🇦 Украинская гривна",
            "RUB": "🇷🇺 Российский рубль",
            "GBP": "🇬🇧 Британский фунт",
            "JPY": "🇯🇵 Японская йена",
            "CNY": "🇨🇳 Китайский юань",
            "KRW": "🇰🇷 Южнокорейская вона",
            "TRY": "🇹🇷 Турецкая лира"
        }

    async def get_exchange_rate(self, base_currency: str) -> dict:
        """Получение курсов валют через API"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.api_url}{base_currency}") as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("result") == "success":
                        return data
                return None

    @app_commands.command(name="currency", description="Показать текущий курс валют")
    @app_commands.describe(валюта="Базовая валюта для отображения курсов (по умолчанию USD)")
    async def exchange_rate(self, interaction: discord.Interaction, валюта: str = "USD"):
        """Показывает текущие курсы валют"""
        await interaction.response.defer()
        
        base_currency = валюта.upper()
        if base_currency not in self.currencies:
            await interaction.followup.send(
                embed=create_embed(
                    description="❌ Указанная валюта не поддерживается!"
                )
            )
            return

        try:
            data = await self.get_exchange_rate(base_currency)
            if not data:
                await interaction.followup.send(
                    embed=create_embed(
                        description="❌ Не удалось получить курсы валют!"
                    )
                )
                return

            rates = data["conversion_rates"]
            description = f"💰 Курсы валют относительно {self.currencies[base_currency]}:\n\n"
            
            for currency, name in self.currencies.items():
                if currency != base_currency:
                    rate = rates[currency]
                    description += f"{EMOJIS['DOT']} **{name}:** `{rate:.2f}`\n"

            embed = create_embed(
                title=f"💱 Курсы валют",
                description=description,
                footer={"text": f"Данные предоставлены ExchangeRate-API • {data['time_last_update_utc'][:10]}"}
            )
            
            await interaction.followup.send(embed=embed)

        except Exception as e:
            print(f"Error in exchange_rate command: {e}")
            await interaction.followup.send(
                embed=create_embed(
                    description="❌ Произошла ошибка при получении курсов валют!"
                )
            )

    @app_commands.command(name="exchange", description="Конвертировать сумму из одной валюты в другую")
    @app_commands.describe(
        amount="Сумма для конвертации",
        from_currency="Исходная валюта",
        to_currency="Целевая валюта"
    )
    async def convert(self, interaction: discord.Interaction, amount: float, from_currency: str, to_currency: str):
        """Конвертирует сумму из одной валюты в другую"""
        await interaction.response.defer()
        
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        if from_currency not in self.currencies or to_currency not in self.currencies:
            await interaction.followup.send(
                embed=create_embed(
                    description="❌ Одна из указанных валют не поддерживается!"
                )
            )
            return

        try:
            data = await self.get_exchange_rate(from_currency)
            if not data:
                await interaction.followup.send(
                    embed=create_embed(
                        description="❌ Не удалось получить курсы валют!"
                    )
                )
                return

            rate = data["conversion_rates"][to_currency]
            converted_amount = amount * rate

            embed = create_embed(
                title="💱 Конвертация валют",
                description=f"{EMOJIS['DOT']} **Сумма:** `{amount:,.2f} {from_currency}`\n"
                          f"{EMOJIS['DOT']} **Курс:** `1 {from_currency} = {rate:.4f} {to_currency}`\n"
                          f"{EMOJIS['DOT']} **Результат:** `{converted_amount:,.2f} {to_currency}`",
                footer={"text": f"Данные предоставлены ExchangeRate-API • {data['time_last_update_utc'][:10]}"}
            )
            
            await interaction.followup.send(embed=embed)

        except Exception as e:
            print(f"Error in convert command: {e}")
            await interaction.followup.send(
                embed=create_embed(
                    description="❌ Произошла ошибка при конвертации валют!"
                )
            )

async def setup(bot):
    await bot.add_cog(Currency(bot)) 