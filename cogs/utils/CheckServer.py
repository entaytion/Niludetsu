import discord
from discord.ext import commands
import yaml

class CheckServer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open("config/config.yaml", "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
            self.allowed_servers = self.config.get('settings', {}).get('allowed_servers', [])
            self.owner_id = self.config.get('settings', {}).get('owner_id')

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