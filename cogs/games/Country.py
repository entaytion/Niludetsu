import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.utils.embed import Embed
import random

# База данных стран и их флагов
COUNTRIES = {
    "Украина": "https://flagcdn.com/w2560/ua.png",
    "Польша": "https://flagcdn.com/w2560/pl.png",
    "Швеция": "https://flagcdn.com/w2560/se.png",
    "Норвегия": "https://flagcdn.com/w2560/no.png",
    "Финляндия": "https://flagcdn.com/w2560/fi.png",
    "Португалия": "https://flagcdn.com/w2560/pt.png",
    "Греция": "https://flagcdn.com/w2560/gr.png",
    "Турция": "https://flagcdn.com/w2560/tr.png",
    "Египет": "https://flagcdn.com/w2560/eg.png",
    "Казахстан": "https://flagcdn.com/w2560/kz.png",
    "Россия": "https://flagcdn.com/w2560/ru.png",
    "США": "https://flagcdn.com/w2560/us.png",
    "Китай": "https://flagcdn.com/w2560/cn.png",
    "Япония": "https://flagcdn.com/w2560/jp.png",
    "Германия": "https://flagcdn.com/w2560/de.png",
    "Франция": "https://flagcdn.com/w2560/fr.png",
    "Великобритания": "https://flagcdn.com/w2560/gb.png",
    "Италия": "https://flagcdn.com/w2560/it.png",
    "Канада": "https://flagcdn.com/w2560/ca.png",
    "Австралия": "https://flagcdn.com/w2560/au.png",
    "Бразилия": "https://flagcdn.com/w2560/br.png",
    "Индия": "https://flagcdn.com/w2560/in.png",
    "Испания": "https://flagcdn.com/w2560/es.png",
    "Мексика": "https://flagcdn.com/w2560/mx.png",
    "Южная Корея": "https://flagcdn.com/w2560/kr.png"
}

class Country(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="country", description="Игра 'Угадай страну по флагу'")
    async def country(self, interaction: discord.Interaction):
        country = random.choice(list(COUNTRIES.keys()))
        flag_url = COUNTRIES[country]
        
        embed=Embed(
            title="🌍 Угадай страну по флагу",
            description="Напишите название страны, флаг которой изображен на картинке",
            color="BLUE"
        )
        embed.set_image(url=flag_url)
        
        await interaction.response.send_message(embed=embed)
        
        def check(message):
            return (
                message.channel == interaction.channel and 
                not message.author.bot and 
                message.content.lower().strip() == country.lower()
            )
        
        try:
            message = await self.bot.wait_for('message', check=check, timeout=30.0)
            
            embed=Embed(
                title="🎉 Поздравляем!",
                description=f"{message.author.mention}, вы угадали! Это действительно **{country}**!",
                color="GREEN"
            )
            embed.set_image(url=flag_url)
            
            await message.reply(embed=embed)
            
        except TimeoutError:
            embed=Embed(
                title="❌ Время вышло!",
                description=f"Никто не угадал. Это была страна **{country}**",
                color="RED"
            )
            embed.set_image(url=flag_url)
            
            await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Country(bot)) 