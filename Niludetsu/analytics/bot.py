import platform
import psutil
import discord
import time
from datetime import timedelta
from .base import BaseAnalytics
from Niludetsu.utils.constants import Emojis
from Niludetsu.utils.embed import Embed

class BotAnalytics(BaseAnalytics):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.start_time = time.time()
        
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
        
    def get_bot_uptime(self):
        """Получить время работы бота"""
        current_time = time.time()
        difference = int(round(current_time - self.start_time))
        return str(timedelta(seconds=difference))
        
    async def generate_analytics(self, ctx):
        """Генерирует аналитику бота"""
        system_info = self.get_system_info()
        
        # Создаем эмбед
        embed = Embed(
            title=f"{Emojis.BOT} Статистика бота {self.bot.user.name}",
            description=f"{Emojis.INFO} Многофункциональный бот для вашего сервера!"
        )
        
        # Основная статистика
        total_guilds = len(self.bot.guilds)
        total_users = sum(g.member_count for g in self.bot.guilds)
        
        embed.add_field(
            name=f"{Emojis.STATS} Основная информация",
            value=f"{Emojis.DOT} **Серверов:** `{total_guilds}`\n"
                  f"{Emojis.DOT} **Пользователей:** `{total_users}`\n"
                  f"{Emojis.DOT} **Команд:** `{len(self.bot.tree.get_commands())}`\n"
                  f"{Emojis.DOT} **Пинг:** `{round(self.bot.latency * 1000)}ms`\n"
                  f"{Emojis.DOT} **Аптайм:** `{self.get_bot_uptime()}`",
            inline=False
        )
        
        # Системная информация
        embed.add_field(
            name=f"{Emojis.PC} Системная информация",
            value=f"{Emojis.DOT} **ОС:** `{system_info['os']}`\n"
                  f"{Emojis.DOT} **Python:** `{system_info['python']}`\n"
                  f"{Emojis.DOT} **Discord.py:** `{discord.__version__}`\n"
                  f"{Emojis.DOT} **CPU:** `{system_info['cpu']}%`\n"
                  f"{Emojis.DOT} **RAM:** `{system_info['memory']}%`\n"
                  f"{Emojis.DOT} **Диск:** `{system_info['disk']}%`",
            inline=False
        )
        
        # Ссылки
        embed.add_field(
            name=f"{Emojis.LINK} Полезные ссылки",
            value=f"{Emojis.DOT} [Сервер поддержки](https://discord.gg/HxwZ6ceKKj)\n"
                  f"{Emojis.DOT} [GitHub](https://github.com/entaytion/Niludetsu)",
            inline=False
        )
        
        # Добавляем аватар бота
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        
        # Добавляем футер
        embed.set_footer(text=f"ID: {self.bot.user.id} • Создан")
        embed.timestamp = self.bot.user.created_at
        
        return embed 