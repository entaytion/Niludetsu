import discord
from discord.ext import commands
import json
import os

class CheckServer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.allowed_servers = self._load_allowed_servers()
    
    def _load_allowed_servers(self):
        """Загружает список разрешенных серверов из файла"""
        if not os.path.exists('config/allowed_servers.json'):
            # Создаем файл с дефолтными значениями если его нет
            default_data = {
                "allowed_servers": [
                    # Список ID разрешенных серверов
                    1125344221587574866
                ],
                "owner_id": 636570363605680139  # ID владельца бота
            }
            os.makedirs('config', exist_ok=True)
            with open('config/allowed_servers.json', 'w') as f:
                json.dump(default_data, f, indent=4)
            return default_data["allowed_servers"]
        
        # Загружаем существующий список
        with open('config/allowed_servers.json', 'r') as f:
            data = json.load(f)
            return data["allowed_servers"]

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """Срабатывает когда бота добавляют на сервер"""
        if guild.id not in self.allowed_servers:
            # Находим первый текстовый канал
            notification_channel = next(
                (channel for channel in guild.text_channels if channel.permissions_for(guild.me).send_messages),
                None
            )
            
            # Отправляем сообщение перед выходом
            if notification_channel:
                embed = discord.Embed(
                    title="⚠️ Ограниченный доступ",
                    description="Извините, но этот бот является приватным и может использоваться только на определенных серверах.\n\nБот будет отключен через несколько секунд.",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="Для владельцев серверов",
                    value="Если вы хотите использовать этого бота, пожалуйста, свяжитесь с его владельцем."
                )
                
                try:
                    await notification_channel.send(embed=embed)
                except:
                    pass  # Игнорируем ошибки отправки
            
            # Выходим из сервера
            try:
                await guild.leave()
                print(f"🚫 Бот покинул неразрешенный сервер: {guild.name} (ID: {guild.id})")
            except:
                print(f"❌ Не удалось покинуть неразрешенный сервер: {guild.name} (ID: {guild.id})")
        else:
            print(f"✅ Бот добавлен на разрешенный сервер: {guild.name} (ID: {guild.id})")

    @commands.Cog.listener()
    async def on_ready(self):
        """Проверяем все сервера при запуске бота"""
        for guild in self.bot.guilds:
            if guild.id not in self.allowed_servers:
                # Находим первый текстовый канал
                notification_channel = next(
                    (channel for channel in guild.text_channels if channel.permissions_for(guild.me).send_messages),
                    None
                )
                
                # Отправляем уведомление
                if notification_channel:
                    embed = discord.Embed(
                        title="⚠️ Ограниченный доступ",
                        description="Извините, но этот бот является приватным и может использоваться только на определенных серверах.\n\nБот будет отключен через несколько секунд.",
                        color=discord.Color.red()
                    )
                    embed.add_field(
                        name="Для владельцев серверов",
                        value="Если вы хотите использовать этого бота, пожалуйста, свяжитесь с его владельцем."
                    )
                    
                    try:
                        await notification_channel.send(embed=embed)
                    except:
                        pass
                
                # Выходим из сервера
                try:
                    await guild.leave()
                    print(f"🚫 Бот покинул неразрешенный сервер при запуске: {guild.name} (ID: {guild.id})")
                except:
                    print(f"❌ Не удалось покинуть неразрешенный сервер при запуске: {guild.name} (ID: {guild.id})")

async def setup(bot):
    await bot.add_cog(CheckServer(bot)) 