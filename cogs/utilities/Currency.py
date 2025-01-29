import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.utils.embed import create_embed
from Niludetsu.utils.emojis import EMOJIS
from Niludetsu.api.Currency import CurrencyAPI

class Currency(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.currency_api = CurrencyAPI()

    @app_commands.command(name="currency", description="Показать текущий курс валют")
    @app_commands.describe(валюта="Базовая валюта для отображения курсов (по умолчанию USD)")
    async def exchange_rate(self, interaction: discord.Interaction, валюта: str = "USD"):
        """Показывает текущие курсы валют"""
        await interaction.response.defer()
        
        base_currency = валюта.upper()
        if not self.currency_api.is_supported_currency(base_currency):
            await interaction.followup.send(
                embed=create_embed(
                    description="❌ Указанная валюта не поддерживается!"
                )
            )
            return

        data = await self.currency_api.get_exchange_rate(base_currency)
        if not data:
            await interaction.followup.send(
                embed=create_embed(
                    description="❌ Не удалось получить курсы валют!"
                )
            )
            return

        rates = data["conversion_rates"]
        description = f"💰 Курсы валют относительно {self.currency_api.get_currency_name(base_currency)}:\n\n"
        
        for currency, name in self.currency_api.currencies.items():
            if currency != base_currency:
                rate = rates[currency]
                description += f"{EMOJIS['DOT']} **{name}:** `{rate:.2f}`\n"

        embed = create_embed(
            title=f"💱 Курсы валют",
            description=description,
            footer={"text": f"Данные предоставлены ExchangeRate-API • {data['time_last_update_utc'][:10]}"}
        )
        
        await interaction.followup.send(embed=embed)

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

        if not self.currency_api.is_supported_currency(from_currency) or not self.currency_api.is_supported_currency(to_currency):
            await interaction.followup.send(
                embed=create_embed(
                    description="❌ Одна из указанных валют не поддерживается!"
                )
            )
            return

        data = await self.currency_api.get_exchange_rate(from_currency)
        if not data:
            await interaction.followup.send(
                embed=create_embed(
                    description="❌ Не удалось получить курсы валют!"
                )
            )
            return

        rate = data["conversion_rates"][to_currency]
        converted_amount = amount * rate

        description = (
            f"💱 **Конвертация валют:**\n\n"
            f"{amount:.2f} {self.currency_api.get_currency_name(from_currency)} = \n"
            f"{converted_amount:.2f} {self.currency_api.get_currency_name(to_currency)}"
        )

        embed = create_embed(
            description=description,
            footer={"text": f"Курс: 1 {from_currency} = {rate:.4f} {to_currency}"}
        )
        
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Currency(bot)) 