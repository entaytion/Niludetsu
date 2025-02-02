import discord
from discord import app_commands
from discord.ext import commands
import socket
import whois
import requests
from datetime import datetime
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.constants import Emojis

class WhoIs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="whois", description="Получить информацию о домене или IP-адресе")
    @app_commands.describe(target="Домен или IP-адрес для поиска")
    async def whois(self, interaction: discord.Interaction, target: str):
        await interaction.response.defer()

        # Проверяем, является ли target IP-адресом
        try:
            socket.inet_aton(target)
            is_ip = True
        except socket.error:
            is_ip = False

        embed=Embed(title=f"🔍 WhoIs информация для {target}")
        
        if is_ip:
            # Получаем информацию об IP
            ip_info = requests.get(f"http://ip-api.com/json/{target}").json()
            
            if ip_info["status"] == "success":
                embed.add_field(name="IP", value=target, inline=True)
                embed.add_field(name="Страна", value=ip_info.get("country", "Неизвестно"), inline=True)
                embed.add_field(name="Регион", value=ip_info.get("regionName", "Неизвестно"), inline=True)
                embed.add_field(name="Город", value=ip_info.get("city", "Неизвестно"), inline=True)
                embed.add_field(name="Провайдер", value=ip_info.get("isp", "Неизвестно"), inline=True)
                embed.add_field(name="Организация", value=ip_info.get("org", "Неизвестно"), inline=True)
                embed.add_field(name="Временная зона", value=ip_info.get("timezone", "Неизвестно"), inline=True)
                embed.add_field(name="Координаты", value=f"{ip_info.get('lat', 'N/A')}, {ip_info.get('lon', 'N/A')}", inline=True)
        else:
            # Получаем информацию о домене
            domain_info = whois.whois(target)
            
            embed.add_field(name="Домен", value=target, inline=True)
            embed.add_field(name="Регистратор", value=domain_info.registrar or "Неизвестно", inline=True)
            
            if isinstance(domain_info.creation_date, list):
                creation_date = domain_info.creation_date[0]
            else:
                creation_date = domain_info.creation_date
                
            if creation_date:
                embed.add_field(name="Дата создания", value=creation_date.strftime("%d.%m.%Y"), inline=True)
            
            if isinstance(domain_info.expiration_date, list):
                expiration_date = domain_info.expiration_date[0]
            else:
                expiration_date = domain_info.expiration_date
                
            if expiration_date:
                embed.add_field(name="Дата истечения", value=expiration_date.strftime("%d.%m.%Y"), inline=True)
            
            if domain_info.name_servers:
                if isinstance(domain_info.name_servers, list):
                    ns = "\n".join(domain_info.name_servers[:3])
                else:
                    ns = domain_info.name_servers
                embed.add_field(name="Серверы имён", value=ns, inline=False)

        embed.set_footer(text=f"Запрошено: {interaction.user.name}")
        embed.timestamp = datetime.now()
        
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(WhoIs(bot)) 