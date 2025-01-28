import discord
from discord.ext import commands
from Niludetsu.utils.embed import create_embed
from mcstatus import JavaServer

class MCServer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="mcserver", description="Получить информацию о сервере Minecraft")
    @discord.app_commands.describe(ip="IP-адрес сервера")
    async def mcserver(self, interaction: discord.Interaction, ip: str):
        await interaction.response.defer()
        
        try:
            server = JavaServer.lookup(ip)
            status = await server.async_status()
            
            # Получаем информацию о сервере
            online = status.players.online
            max_players = status.players.max
            version = status.version.name
            latency = round(status.latency, 2)
            
            # Создаем описание
            description = [
                f"**Версия:** {version}",
                f"**Игроки:** {online}/{max_players}",
                f"**Пинг:** {latency}ms"
            ]
            
            # Добавляем список игроков, если они есть
            if status.players.sample:
                players = [player.name for player in status.players.sample]
                description.append(f"\n**Онлайн игроки:**\n" + "\n".join(players))
            
            await interaction.followup.send(
                embed=create_embed(
                    title=f"Информация о сервере {ip}",
                    description="\n".join(description),
                    color="GREEN" if online > 0 else "RED"
                )
            )
            
        except Exception as e:
            print(f"Ошибка при получении информации о сервере: {e}")
            await interaction.followup.send(
                embed=create_embed(
                    description="Не удалось получить информацию о сервере. Проверьте IP-адрес и убедитесь, что сервер онлайн.",
                    color="RED"
                ),
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(MCServer(bot)) 