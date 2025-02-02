from ..utils.logging import BaseLogger
from ..utils.constants import Emojis
import discord
from typing import Optional

class WebhookLogger(BaseLogger):
    """Логгер для вебхуков Discord."""
    
    async def log_webhook_update(self, channel: discord.TextChannel):
        """Логирование обновления вебхуков в канале"""
        try:
            # Получаем текущие вебхуки канала
            current_webhooks = await channel.webhooks()
            
            # Создаем эмбед
            fields = [
                {"name": f"{Emojis.DOT} Канал", "value": channel.mention, "inline": True},
                {"name": f"{Emojis.DOT} ID канала", "value": str(channel.id), "inline": True},
                {"name": f"{Emojis.DOT} Количество вебхуков", "value": str(len(current_webhooks)), "inline": True}
            ]
            
            # Добавляем список вебхуков
            if current_webhooks:
                webhook_list = "\n".join([f"• {webhook.name} (ID: {webhook.id})" for webhook in current_webhooks])
                if len(webhook_list) > 1024:  # Ограничение Discord для поля
                    webhook_list = webhook_list[:1021] + "..."
                fields.append({"name": f"{Emojis.DOT} Активные вебхуки", "value": webhook_list, "inline": False})
            
            await self.log_event(
                title=f"{Emojis.INFO} Обновление вебхуков",
                description=f"Обнаружено обновление вебхуков в канале {channel.mention}",
                color='BLUE',
                fields=fields,
                event_type="webhook_update"
            )
            
        except Exception as e:
            print(f"Ошибка при логировании обновления вебхуков: {e}")
    
    async def log_webhook_create(self, webhook: discord.Webhook, creator: Optional[discord.Member] = None):
        """Логирование создания вебхука"""
        fields = [
            {"name": f"{Emojis.DOT} Название", "value": webhook.name, "inline": True},
            {"name": f"{Emojis.DOT} ID", "value": str(webhook.id), "inline": True},
            {"name": f"{Emojis.DOT} Канал", "value": webhook.channel.mention, "inline": True},
            {"name": f"{Emojis.DOT} Создатель", "value": creator.mention if creator else "Неизвестно", "inline": True}
        ]
        
        await self.log_event(
            title=f"{Emojis.SUCCESS} Создан новый вебхук",
            description=f"В канале {webhook.channel.mention} создан новый вебхук",
            color='GREEN',
            fields=fields,
            thumbnail_url=webhook.avatar.url if webhook.avatar else None
        )
        
    async def log_webhook_avatar_update(self, before: discord.Webhook, after: discord.Webhook):
        """Логирование изменения аватара вебхука"""
        fields = [
            {"name": f"{Emojis.DOT} Название", "value": after.name, "inline": True},
            {"name": f"{Emojis.DOT} ID", "value": str(after.id), "inline": True},
            {"name": f"{Emojis.DOT} Канал", "value": after.channel.mention, "inline": True}
        ]
        
        await self.log_event(
            title=f"{Emojis.INFO} Изменен аватар вебхука",
            description=f"Обновлен аватар вебхука в канале {after.channel.mention}",
            color='BLUE',
            fields=fields,
            thumbnail_url=after.avatar.url if after.avatar else None,
            image_url=before.avatar.url if before.avatar else None
        )
        
    async def log_webhook_name_update(self, before: discord.Webhook, after: discord.Webhook):
        """Логирование изменения названия вебхука"""
        fields = [
            {"name": f"{Emojis.DOT} ID", "value": str(after.id), "inline": True},
            {"name": f"{Emojis.DOT} Старое название", "value": before.name, "inline": True},
            {"name": f"{Emojis.DOT} Новое название", "value": after.name, "inline": True},
            {"name": f"{Emojis.DOT} Канал", "value": after.channel.mention, "inline": True}
        ]
        
        await self.log_event(
            title=f"{Emojis.INFO} Изменено название вебхука",
            description=f"Обновлено название вебхука в канале {after.channel.mention}",
            color='BLUE',
            fields=fields,
            thumbnail_url=after.avatar.url if after.avatar else None
        )
        
    async def log_webhook_channel_update(self, before: discord.Webhook, after: discord.Webhook):
        """Логирование изменения канала вебхука"""
        fields = [
            {"name": f"{Emojis.DOT} Название", "value": after.name, "inline": True},
            {"name": f"{Emojis.DOT} ID", "value": str(after.id), "inline": True},
            {"name": f"{Emojis.DOT} Старый канал", "value": before.channel.mention, "inline": True},
            {"name": f"{Emojis.DOT} Новый канал", "value": after.channel.mention, "inline": True}
        ]
        
        await self.log_event(
            title=f"{Emojis.INFO} Изменен канал вебхука",
            description=f"Вебхук перемещен в другой канал",
            color='BLUE',
            fields=fields,
            thumbnail_url=after.avatar.url if after.avatar else None
        )
        
    async def log_webhook_delete(self, webhook: discord.Webhook):
        """Логирование удаления вебхука"""
        fields = [
            {"name": f"{Emojis.DOT} Название", "value": webhook.name, "inline": True},
            {"name": f"{Emojis.DOT} ID", "value": str(webhook.id), "inline": True},
            {"name": f"{Emojis.DOT} Канал", "value": webhook.channel.mention, "inline": True}
        ]
        
        await self.log_event(
            title=f"{Emojis.ERROR} Вебхук удален",
            description=f"Удален вебхук из канала {webhook.channel.mention}",
            color='RED',
            fields=fields,
            thumbnail_url=webhook.avatar.url if webhook.avatar else None
        ) 