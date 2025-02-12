import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
from typing import Optional
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.constants import Emojis
import re

class Links(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.isgd_api = "https://is.gd/create.php"
        self.unshorten_api = "https://unshorten.me/json/"
        self.url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )
        
    links_group = app_commands.Group(name="links", description="Управление ссылками")
    
    @links_group.command(name="short", description="Сократить ссылку")
    @app_commands.describe(url="Ссылка для сокращения")
    async def short_slash(self, interaction: discord.Interaction, url: str):
        """Сократить ссылку через is.gd"""
        await interaction.response.defer()
        
        # Проверяем, является ли ввод действительной ссылкой
        if not self.url_pattern.match(url):
            embed = Embed(
                title="❌ Ошибка",
                description="Указанная ссылка недействительна",
                color=0xe74c3c
            )
            return await interaction.followup.send(embed=embed)
            
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    'format': 'json',
                    'url': url
                }
                async with session.get(self.isgd_api, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'shorturl' in data:
                            embed = Embed(
                                title=f"{Emojis.SUCCESS} Ссылка сокращена",
                                description=f"{Emojis.DOT} **Оригинал:** {url}\n"
                                          f"{Emojis.DOT} **Сокращенная:** {data['shorturl']}",
                                color="DEFAULT"
                            )
                            return await interaction.followup.send(embed=embed)
                    
                    embed = Embed(
                        title="❌ Ошибка",
                        description="Не удалось сократить ссылку",
                        color=0xe74c3c
                    )
                    return await interaction.followup.send(embed=embed)
                    
        except Exception as e:
            embed = Embed(
                title="❌ Ошибка",
                description=f"Произошла ошибка: {str(e)}",
                color=0xe74c3c
            )
            return await interaction.followup.send(embed=embed)
            
    @links_group.command(name="unshort", description="Развернуть сокращенную ссылку")
    @app_commands.describe(url="Сокращенная ссылка")
    async def unshort_slash(self, interaction: discord.Interaction, url: str):
        """Развернуть сокращенную ссылку используя unshorten.me"""
        await interaction.response.defer()
        
        # Проверяем, является ли ввод действительной ссылкой
        if not self.url_pattern.match(url):
            embed = Embed(
                title="❌ Ошибка",
                description="Указанная ссылка недействительна",
                color=0xe74c3c
            )
            return await interaction.followup.send(embed=embed)
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.unshorten_api}{url}") as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success'):
                            resolved_url = data.get('resolved_url')
                            
                            # Проверяем, отличается ли оригинальная ссылка от сокращенной
                            if resolved_url and resolved_url != url:
                                embed = Embed(
                                    title=f"{Emojis.SUCCESS} Ссылка развернута",
                                    description=f"{Emojis.DOT} **Сокращенная:** {url}\n"
                                              f"{Emojis.DOT} **Оригинал:** {resolved_url}",
                                    color="DEFAULT"
                                )
                                return await interaction.followup.send(embed=embed)
                            else:
                                embed = Embed(
                                    title="ℹ️ Информация",
                                    description="Это не сокращенная ссылка или она уже развернута",
                                    color=0x3498db
                                )
                                return await interaction.followup.send(embed=embed)
                    
                    embed = Embed(
                        title="❌ Ошибка",
                        description="Не удалось развернуть ссылку",
                        color=0xe74c3c
                    )
                    return await interaction.followup.send(embed=embed)
                    
        except Exception as e:
            embed = Embed(
                title="❌ Ошибка",
                description=f"Произошла ошибка: {str(e)}",
                color=0xe74c3c
            )
            return await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Links(bot)) 