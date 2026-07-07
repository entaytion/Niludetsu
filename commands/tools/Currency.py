import discord, re
from discord import app_commands
from discord.ext import commands
from Niludetsu import Embed, Emojis
from Niludetsu.api.Currency import CurrencyAPI
from Niludetsu.locale import _
from typing import Tuple

class CurrencyHelper:
    """Вспомогательный класс для работы с валютами"""

    # Регулярные выражения для распознавания валют
    CURRENCY_PATTERNS = {
        "RUB": r"(?:руб(?:л(?:ь|я|ей|ъ|eй|и(?:ки|шек|шки)?)?)?|₽|руб\.)",
        "USD": r"(?:долл?ар(?:ов|а|ы)?|бакс(?:ов|а|ы)?|\$|usd|dollar)",
        "EUR": r"(?:евр(?:о|ик|ы|а)|€|eur(?:o|os)?)",
        "UAH": r"(?:грив(?:ен|на|ень|н|ня|ни|ней|ны|нов|еней)|грн\.|\bгрн\b|₴)",
        "BYN": r"(?:\bбелорусских\b|\bбел\.?руб(?:л(?:ей|ь|и)?)?\b|\bбр\.?\b|\bбын\b|\bбун(?:ов|а|ы)?\b)",
        "KZT": r"(?:тенг(?:е|и|ов|а)?|тг|₸|тнг\.?)",
        "GBP": r"(?:фунт(?:ов|а|ы)?|£|gbp)",
        "JPY": r"(?:иен(?:а|ы|ей)?|¥|jpy)",
        "CNY": r"(?:юан(?:ей|я|и)?|cny)",
        "KRW": r"(?:вон(?:а|ы)?|krw)",
        "TRY": r"(?:лир(?:а|ы|ей)?|try)",
        "UZS": r"(?:узс|\buzs\b|сум(?:а|ы|ов)?|сўм|so['']m|\bsom\b)",
    }

    def __init__(self):
        currency_patterns = [f"(?P<{code}>{pattern})" for code, pattern in self.CURRENCY_PATTERNS.items()]
        all_currencies = '|'.join(currency_patterns)

        self.money_pattern = re.compile(
            rf'(?P<amount>\d+(?:[.,]\d+)?)\s*({all_currencies})',
            re.IGNORECASE
        )

    def get_currency_code(self, query: str) -> str:
        """Определяет код валюты из текста"""
        query = query.lower().strip()

        for code, pattern in self.CURRENCY_PATTERNS.items():
            if re.match(f"^{pattern}$", query, re.IGNORECASE):
                return code
        return query.upper()

    def find_currency_mentions(self, text: str) -> dict:
        """Находит упоминания валют в тексте"""
        matches = self.money_pattern.finditer(text)
        found_currencies = {}

        for match in matches:
            amount_str = match.group('amount')
            amount = float(amount_str.replace(',', '.'))

            found_currency = None
            for code in self.CURRENCY_PATTERNS.keys():
                if match.group(code):
                    found_currency = code
                    break

            if found_currency:
                found_currencies.setdefault(found_currency, []).append(amount)

        return found_currencies


class Currency(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.currency_api = CurrencyAPI()
        self.currency_helper = CurrencyHelper()

    def extract_amount_and_currency(self, text: str) -> Tuple[float, str]:
        found_currencies = self.currency_helper.find_currency_mentions(text)
        if found_currencies:
            currency = next(iter(found_currencies))
            amount = found_currencies[currency][0]
            return amount, currency
        return 0, ""

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.content.startswith(('/', '!')):
            return
        if not message.guild or message.guild.id != 1125344221587574866:
            return

        found_currencies = self.currency_helper.find_currency_mentions(message.content)
        if not found_currencies:
            return

        t = _(guild_id=message.guild.id, bot=self.bot)

        for from_currency, amounts in found_currencies.items():
            total_amount = sum(amounts)

            data = await self.currency_api.get_exchange_rate(from_currency)
            if not data:
                continue

            rates = data["conversion_rates"]

            conversions = []
            for to_currency in ["USD", "EUR", "RUB", "UAH", "BYN", "KZT", "UZS"]:
                if to_currency != from_currency and to_currency in rates:
                    rate = rates[to_currency]
                    converted = total_amount * rate
                    conversions.append(f"{Emojis.DOT} {converted:.2f} {self.currency_api.get_currency_name(to_currency)}")

            embed = Embed(
                title=t('tools', 'currency_title'),
                description=f"**{total_amount:.2f} {self.currency_api.get_currency_name(from_currency)}:**\n" + "\n".join(conversions)
            )
            await message.reply(embed=embed, mention_author=False, delete_after=5)

    @app_commands.command(name="currency", description="Показать текущий курс валют")
    @app_commands.describe(
        валюта="Базовая валюта для отображения курсов (по умолчанию USD)",
        сумма="Сумма для конвертации (необязательно)"
    )
    async def exchange_rate(self, interaction: discord.Interaction, валюта: str = "USD", сумма: float = None):
        await interaction.response.defer()

        t = _(guild_id=interaction.guild_id, bot=self.bot)

        base_currency = валюта.upper()
        if not self.currency_api.is_supported_currency(base_currency):
            await interaction.followup.send(embed=Embed.error(description=t('tools', 'currency_not_supported')))
            return

        data = await self.currency_api.get_exchange_rate(base_currency)
        if not data:
            await interaction.followup.send(embed=Embed.error(description=t('tools', 'currency_api_error')))
            return

        rates = data["conversion_rates"]
        description = t('tools', 'currency_rates_desc', base=self.currency_api.get_currency_name(base_currency))
        if сумма:
            description += t('tools', 'currency_rates_for', amount=f"{сумма:,.2f}")
        description += ":\n\n"

        for currency, name in self.currency_api.currencies.items():
            if currency != base_currency and currency in rates:
                rate = rates[currency]
                if сумма:
                    converted = rate * сумма
                    description += f"{Emojis.DOT} **{name}:** `{rate:.2f}` ({converted:,.2f})\n"
                else:
                    description += f"{Emojis.DOT} **{name}:** `{rate:.2f}`\n"

        embed = Embed(
            title=t('tools', 'currency_rates_title'),
            description=description,
            footer={"text": t('tools', 'currency_data_footer', date=data['time_last_update_utc'][:10])}
        )
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="exchange", description="Конвертировать сумму из одной валюты в другую")
    @app_commands.describe(
        amount="Сумма для конвертации",
        from_currency="Исходная валюта (например: RUB, руб, рублей)",
        to_currency="Целевая валюта (например: USD, $, доллар)"
    )
    async def convert(self, interaction: discord.Interaction, amount: float, from_currency: str, to_currency: str):
        await interaction.response.defer()

        t = _(guild_id=interaction.guild_id, bot=self.bot)

        from_currency = self.currency_helper.get_currency_code(from_currency)
        to_currency = self.currency_helper.get_currency_code(to_currency)

        if not self.currency_api.is_supported_currency(from_currency) or not self.currency_api.is_supported_currency(to_currency):
            await interaction.followup.send(embed=Embed.error(description=t('tools', 'currency_unsupported_one')))
            return

        data = await self.currency_api.get_exchange_rate(from_currency)
        if not data:
            await interaction.followup.send(embed=Embed.error(description=t('tools', 'currency_api_error')))
            return

        rate = data["conversion_rates"][to_currency]
        converted_amount = amount * rate

        embed = Embed(
            description=(
                f"{t('tools', 'currency_convert_title')}\n\n"
                f"{amount:,.2f} {self.currency_api.get_currency_name(from_currency)} = \n"
                f"{converted_amount:,.2f} {self.currency_api.get_currency_name(to_currency)}"
            ),
            footer={"text": t('tools', 'currency_exchange_footer', from_cur=from_currency, rate=f"{rate:.4f}", to_cur=to_currency)}
        )
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Currency(bot))
