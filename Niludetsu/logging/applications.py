from ..core.base import BaseLogger, EMOJIS
import discord
from typing import Optional, Union
import yaml
import traceback

class ApplicationLogger(BaseLogger):
    """Логгер для событий, связанных с приложениями Discord."""
    
    def __init__(self, bot):
        super().__init__(bot)
        self.log_channel_id: Optional[int] = None
        self.webhook_url: Optional[str] = None
        bot.loop.create_task(self.initialize_logs())
        
    async def initialize_logs(self):
        """Инициализация канала логов"""
        await self.bot.wait_until_ready()
        try:
            with open('config/config.yaml', 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                if 'logging' in config and 'main_channel' in config['logging']:
                    channel_id = int(config['logging']['main_channel'])
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        webhook = await self.get_webhook(channel)
                        if webhook:
                            await self.initialize_webhook(webhook.url)
                            await self.send_log(
                                title="✅ Логгер приложений активирован",
                                description="Система логирования приложений успешно инициализирована",
                                color=0x2ECC71
                            )
        except Exception as e:
            print(f"❌ Ошибка при инициализации логгера приложений: {e}")
            
    async def get_webhook(self, channel: discord.TextChannel) -> Optional[discord.Webhook]:
        """Получение или создание вебхука"""
        try:
            webhooks = await channel.webhooks()
            webhook = discord.utils.get(webhooks, name='NiluBot Logs')
            if not webhook:
                webhook = await channel.create_webhook(name='NiluBot Logs')
            return webhook
        except Exception:
            return None
            
    async def initialize_webhook(self, webhook_url: str):
        """Инициализация вебхука для логирования"""
        self.webhook_url = webhook_url
        
    async def send_log(self, title: str, description: str, color=0x2ECC71):
        """Отправка сообщения в лог"""
        await self.log_event(
            title=title,
            description=description,
            color=color
        )
        
    async def log_app_add(self, app: discord.Integration):
        """Логирование добавления приложения"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Название", "value": app.name, "inline": True},
            {"name": f"{EMOJIS['DOT']} ID", "value": str(app.id), "inline": True},
            {"name": f"{EMOJIS['DOT']} Тип", "value": app.type, "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['SUCCESS']} Добавлено новое приложение",
            description="Приложение было добавлено на сервер",
            color='GREEN',
            fields=fields,
            thumbnail_url=app.icon_url if hasattr(app, 'icon_url') else None
        )
        
    async def log_app_remove(self, app: discord.Integration):
        """Логирование удаления приложения"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Название", "value": app.name, "inline": True},
            {"name": f"{EMOJIS['DOT']} ID", "value": str(app.id), "inline": True},
            {"name": f"{EMOJIS['DOT']} Тип", "value": app.type, "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['ERROR']} Приложение удалено",
            description="Приложение было удалено с сервера",
            color='RED',
            fields=fields,
            thumbnail_url=app.icon_url if hasattr(app, 'icon_url') else None
        )
        
    async def log_app_permission_update(self, app_command):
        """Логирование обновления разрешений команды приложения"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Команда", "value": app_command.name, "inline": True},
            {"name": f"{EMOJIS['DOT']} ID", "value": str(app_command.id), "inline": True},
            {"name": f"{EMOJIS['DOT']} Тип", "value": app_command.type, "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['INFO']} Обновление разрешений команды",
            description="Разрешения команды приложения были обновлены",
            color='BLUE',
            fields=fields
        ) 