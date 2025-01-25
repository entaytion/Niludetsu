import discord
from discord import app_commands
from discord.ext import commands
from mcstatus import JavaServer
from utils import create_embed, EMOJIS
import re

class MCServer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="mcserver", description="Получить информацию о Minecraft сервере")
    @app_commands.describe(address="IP-адрес или домен сервера")
    async def mcserver(self, interaction: discord.Interaction, address: str):
        await interaction.response.defer()

        try:
            # Добавляем порт по умолчанию, если он не указан
            if not re.search(r':\d+$', address):
                address += ':25565'

            # Получаем информацию о сервере
            server = JavaServer.lookup(address)
            status = await server.async_status()
            
            # Создаем эмбед
            embed = create_embed(
                title=f"{EMOJIS.get('MINECRAFT', '🎮')} Информация о сервере {address}"
            )
            
            # Добавляем основную информацию
            embed.add_field(
                name="Статус",
                value=f"{EMOJIS.get('ONLINE', '🟢')} Онлайн",
                inline=True
            )
            
            embed.add_field(
                name="Игроки",
                value=f"{status.players.online}/{status.players.max}",
                inline=True
            )
            
            embed.add_field(
                name="Версия",
                value=status.version.name,
                inline=True
            )
            
            # Добавляем пинг
            embed.add_field(
                name="Пинг",
                value=f"{round(status.latency)} мс",
                inline=True
            )
            
            # Если есть MOTD (описание сервера)
            if hasattr(status, 'description'):
                motd = status.description
                if isinstance(motd, dict) and 'text' in motd:
                    motd = motd['text']
                elif isinstance(motd, str):
                    # Удаляем коды форматирования
                    motd = re.sub(r'§[0-9a-fk-or]', '', motd)
                embed.add_field(
                    name="MOTD",
                    value=motd,
                    inline=False
                )
            
            # Если есть список игроков онлайн
            if status.players.online > 0 and hasattr(status.players, 'sample') and status.players.sample:
                players_list = "\n".join([player.name for player in status.players.sample[:10]])
                if len(status.players.sample) > 10:
                    players_list += f"\n... и ещё {status.players.online - 10} игроков"
                embed.add_field(
                    name="Игроки онлайн",
                    value=players_list,
                    inline=False
                )
            
            # Добавляем иконку сервера, если она есть
            if hasattr(status, 'favicon') and status.favicon:
                embed.set_thumbnail(url=status.favicon)
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            error_embed = create_embed(
                description=f"{EMOJIS['ERROR']} Не удалось получить информацию о сервере: {str(e)}"
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(MCServer(bot)) 