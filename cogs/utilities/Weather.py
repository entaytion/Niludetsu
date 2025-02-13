import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu import Embed, Emojis, WeatherAPI

class Weather(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.weather_api = WeatherAPI()

    @app_commands.command(name="weather", description="Узнать погоду в указанном городе")
    @app_commands.describe(city="Название города")
    async def weather(self, interaction: discord.Interaction, city: str):
        """Показывает текущую погоду в указанном городе"""
        await interaction.response.defer()

        weather_data = await self.weather_api.get_weather(city)
        if not weather_data:
            await interaction.followup.send(
                embed=Embed(
                    description="❌ Не удалось найти указанный город!"
                )
            )
            return

        formatted_data = self.weather_api.format_weather_data(weather_data)
        
        description = (
            f"{formatted_data['icon']} **{formatted_data['description'].capitalize()}**\n\n"
            f"{Emojis.DOT} Температура: `{formatted_data['temp']}°C`\n"
            f"{Emojis.DOT} Ощущается как: `{formatted_data['feels_like']}°C`\n"
            f"{Emojis.DOT} Влажность: `{formatted_data['humidity']}%`\n"
            f"{Emojis.DOT} Ветер: `{formatted_data['wind_speed']} м/с`\n"
            f"{Emojis.DOT} Давление: `{formatted_data['pressure']} мм рт.ст.`\n"
            f"{Emojis.DOT} Видимость: `{formatted_data['visibility']} км`\n"
            f"{Emojis.DOT} Восход: `{formatted_data['sunrise']}`\n"
            f"{Emojis.DOT} Закат: `{formatted_data['sunset']}`"
        )

        embed=Embed(
            title=f"🌍 Погода в городе {formatted_data['city_name']}",
            description=description
        )
        
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Weather(bot))