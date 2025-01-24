import discord
from discord.ext import commands
from discord import app_commands
from utils import create_embed, EMOJIS
import platform
import psutil
import time
import datetime

class BotInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()

    def get_bot_uptime(self):
        """Получить время работы бота"""
        current_time = time.time()
        difference = int(round(current_time - self.start_time))
        return str(datetime.timedelta(seconds=difference))

    def get_system_info(self):
        """Получить информацию о системе"""
        cpu_usage = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "cpu": cpu_usage,
            "memory": memory.percent,
            "disk": disk.percent,
            "python": platform.python_version(),
            "os": f"{platform.system()} {platform.release()}"
        }

    @app_commands.command(name="botinfo", description="Показать информацию о боте")
    async def botinfo(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()

            # Получаем информацию о системе
            system_info = self.get_system_info()
            
            # Создаем основной эмбед
            embed = create_embed(
                title="🤖 Информация о боте",
                description=f"**{self.bot.user.name}** - многофункциональный бот для вашего сервера!"
            )

            # Основная информация
            embed.add_field(
                name="📊 Основная информация",
                value=f"""
{EMOJIS['DOT']} **Серверов**: `{len(self.bot.guilds)}`
{EMOJIS['DOT']} **Пользователей**: `{sum(g.member_count for g in self.bot.guilds)}`
{EMOJIS['DOT']} **Команд**: `{len(self.bot.tree.get_commands())}`
{EMOJIS['DOT']} **Пинг**: `{round(self.bot.latency * 1000)}ms`
{EMOJIS['DOT']} **Аптайм**: `{self.get_bot_uptime()}`
                """,
                inline=False
            )

            # Системная информация
            embed.add_field(
                name="💻 Системная информация",
                value=f"""
{EMOJIS['DOT']} **ОС**: `{system_info['os']}`
{EMOJIS['DOT']} **Python**: `{system_info['python']}`
{EMOJIS['DOT']} **Discord.py**: `{discord.__version__}`
{EMOJIS['DOT']} **CPU**: `{system_info['cpu']}%`
{EMOJIS['DOT']} **RAM**: `{system_info['memory']}%`
{EMOJIS['DOT']} **Диск**: `{system_info['disk']}%`
                """,
                inline=False
            )

            # Ссылки
            embed.add_field(
                name="🔗 Полезные ссылки",
                value=f"""
{EMOJIS['DOT']} [Сервер поддержки](https://discord.gg/HxwZ6ceKKj)
{EMOJIS['DOT']} [GitHub](https://github.com/entaytion/Niludetsu)
                """,
                inline=False
            )

            # Добавляем аватар бота
            embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)

            # Добавляем футер
            embed.set_footer(text=f"ID: {self.bot.user.id} • Создан")
            embed.timestamp = self.bot.user.created_at

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Произошла ошибка: {str(e)}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(BotInfo(bot)) 