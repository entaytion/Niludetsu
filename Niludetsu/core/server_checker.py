import discord
from typing import Optional, List
import yaml
from pathlib import Path
from ..utils.embed import Embed

class ServerChecker:
    def __init__(self, bot):
        self.bot = bot
        self._load_config()
    
    def _load_config(self) -> None:
        """Загрузка конфигурации из файла"""
        with open(Path("data/config.yaml"), "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            self.allowed_servers = config.get('settings', {}).get('allowed_servers', [])
            self.owner_id = config.get('settings', {}).get('owner_id')
    
    async def _send_notification(self, guild: discord.Guild) -> None:
        """Отправка уведомления о выходе с сервера"""
        notification_channel = next(
            (channel for channel in guild.text_channels 
             if channel.permissions_for(guild.me).send_messages),
            None
        )
        
        if notification_channel:
            embed=Embed(
                title="⚠️ Ограниченный доступ",
                description="Извините, но этот бот является приватным и может использоваться только на определенных серверах.\n\nБот будет отключен через несколько секунд.",
                color="RED",
                fields=[{
                    "name": "Для владельцев серверов",
                    "value": f"Если вы хотите использовать этого бота, пожалуйста, свяжитесь с его владельцем <@{self.owner_id}>"
                }]
            )
            
            try:
                await notification_channel.send(embed=embed)
            except Exception:
                pass

    async def check_guild(self, guild: discord.Guild) -> bool:
        """
        Проверка отдельного сервера
        Returns:
            bool: True если сервер разрешен, False если нет
        """
        if guild.id not in self.allowed_servers:
            await self._send_notification(guild)
            try:
                await guild.leave()
                print(f"🚫 Бот покинул неразрешенный сервер: {guild.name} (ID: {guild.id})")
                return False
            except Exception as e:
                print(f"❌ Не удалось покинуть неразрешенный сервер: {guild.name} (ID: {guild.id})")
                return False
        return True

    async def check_all_guilds(self) -> None:
        """Проверка всех серверов, где находится бот"""
        for guild in self.bot.guilds:
            await self.check_guild(guild)

    def is_guild_allowed(self, guild_id: int) -> bool:
        """
        Простая проверка разрешен ли сервер
        Args:
            guild_id (int): ID сервера для проверки
        Returns:
            bool: True если сервер разрешен, False если нет
        """
        return guild_id in self.allowed_servers