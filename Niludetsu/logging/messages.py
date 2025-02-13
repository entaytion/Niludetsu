from Niludetsu import BaseLogger, Emojis, LoggingState
import discord, tempfile, os
from typing import Optional, List, Union
from discord.ext import commands
from datetime import datetime

class MessageLogger(BaseLogger):
    """Логгер для сообщений Discord."""
    
    def __init__(self, bot: discord.Client):
        super().__init__(bot)
        self.log_channel = None
        bot.loop.create_task(self._initialize())
    
    async def _initialize(self):
        """Инициализация логгера"""
        await self.bot.wait_until_ready()
        await self.initialize_logs()
        self.log_channel = LoggingState.log_channel
        
    async def log_message_delete(self, message: discord.Message):
        """Логирование удаления сообщения"""
        if message.author.bot:
            return
            
        fields = [
            {"name": f"{Emojis.DOT} Автор", "value": f"{message.author.mention} (`{message.author.name}`)", "inline": True},
            {"name": f"{Emojis.DOT} Канал", "value": message.channel.mention, "inline": True},
            {"name": f"{Emojis.DOT} ID сообщения", "value": str(message.id), "inline": True}
        ]
        
        if message.content:
            fields.append({"name": f"{Emojis.DOT} Содержание", "value": message.content[:1024], "inline": False})
            
        if message.attachments:
            attachments = "\n".join([f"[{a.filename}]({a.url})" for a in message.attachments])
            fields.append({"name": f"{Emojis.DOT} Вложения", "value": attachments, "inline": False})
            
        await self.log_event(
            title=f"{Emojis.ERROR} Сообщение удалено",
            description=f"Удалено сообщение в канале {message.channel.mention}",
            color='RED',
            fields=fields,
            timestamp=message.created_at
        )
        
    async def log_message_bulk_delete(self, messages: List[discord.Message], channel: discord.TextChannel):
        """Логирование массового удаления сообщений"""
        fields = [
            {"name": f"{Emojis.DOT} Канал", "value": channel.mention, "inline": True},
            {"name": f"{Emojis.DOT} Количество", "value": str(len(messages)), "inline": True}
        ]
        
        # Создаем текстовый файл с удаленными сообщениями
        content = []
        file_content = []
        
        for msg in messages[:10]:  # Показываем только первые 10 сообщений в эмбеде
            author = msg.author.name if msg.author else "Неизвестно"
            content.append(f"**{author}**: {msg.content[:100]}...")
            
        for msg in messages:  # Все сообщения записываем в файл
            author = msg.author.name if msg.author else "Неизвестно"
            timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
            file_content.append(f"[{timestamp}] {author}: {msg.content}")
            if msg.attachments:
                for attachment in msg.attachments:
                    file_content.append(f"[Вложение] {attachment.filename}: {attachment.url}")
            file_content.append("-" * 50)
            
        if content:
            fields.append({"name": f"{Emojis.DOT} Последние сообщения", "value": "\n".join(content), "inline": False})
            
        if len(messages) > 10:
            fields.append({"name": f"{Emojis.DOT} Примечание", "value": "Показаны только последние 10 сообщений. Полный список в прикрепленном файле.", "inline": False})
                    
        temp_file = tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8', suffix='.txt')
        temp_file.write("\n".join(file_content))
        temp_file.close()
        
        file = discord.File(temp_file.name, filename=f"deleted_messages_{channel.name}_{len(messages)}.txt")
        
        await self.log_event(
            title=f"{Emojis.ERROR} Массовое удаление сообщений",
            description=f"Удалено {len(messages)} сообщений в канале {channel.mention}",
            color='RED',
            fields=fields,
            file=file
        )
        
        # Удаляем временный файл
        os.unlink(temp_file.name)
        
    async def log_message_edit(self, before: discord.Message, after: discord.Message):
        """Логирование изменения сообщения"""
        if before.author.bot or before.content == after.content:
            return
            
        fields = [
            {"name": f"{Emojis.DOT} Автор", "value": f"{before.author.mention} (`{before.author.name}`)", "inline": True},
            {"name": f"{Emojis.DOT} Канал", "value": before.channel.mention, "inline": True},
            {"name": f"{Emojis.DOT} ID сообщения", "value": str(before.id), "inline": True},
            {"name": f"{Emojis.DOT} До", "value": before.content[:1024] if before.content else "*пусто*", "inline": False},
            {"name": f"{Emojis.DOT} После", "value": after.content[:1024] if after.content else "*пусто*", "inline": False}
        ]
        
        await self.log_event(
            title=f"{Emojis.INFO} Сообщение изменено",
            description=f"Изменено сообщение в канале {before.channel.mention}",
            color='BLUE',
            fields=fields,
            timestamp=after.edited_at or datetime.now()
        )
        
    async def log_message_publish(self, message: discord.Message):
        """Логирование публикации сообщения в новостном канале"""
        fields = [
            {"name": f"{Emojis.DOT} Автор", "value": message.author.mention, "inline": True},
            {"name": f"{Emojis.DOT} Канал", "value": message.channel.mention, "inline": True},
            {"name": f"{Emojis.DOT} Ссылка", "value": f"[Перейти]({message.jump_url})", "inline": True}
        ]
        
        if message.content:
            fields.append({"name": f"{Emojis.DOT} Содержание", "value": message.content[:1024], "inline": False})
            
        if message.attachments:
            attachments = "\n".join([f"[{a.filename}]({a.url})" for a in message.attachments])
            fields.append({"name": f"{Emojis.DOT} Вложения", "value": attachments, "inline": False})
            
        await self.log_event(
            title=f"{Emojis.SUCCESS} Сообщение опубликовано",
            description=f"Опубликовано сообщение из канала {message.channel.mention}",
            color='GREEN',
            fields=fields
        )
        
    async def log_message_command(self, ctx: Union[commands.Context, discord.Interaction], command_name: str):
        """Логирование использования команды"""
        if isinstance(ctx, discord.Interaction):
            user = ctx.user
            channel = ctx.channel
            command = f"/{command_name}"
        else:
            user = ctx.author
            channel = ctx.channel
            command = ctx.message.content
            
        fields = [
            {"name": f"{Emojis.DOT} Пользователь", "value": user.mention, "inline": True},
            {"name": f"{Emojis.DOT} Канал", "value": channel.mention, "inline": True},
            {"name": f"{Emojis.DOT} Команда", "value": f"`{command}`", "inline": True}
        ]
        
        await self.log_event(
            title=f"{Emojis.INFO} Использована команда",
            description=f"Пользователь использовал команду в канале {channel.mention}",
            color='BLUE',
            fields=fields
        )

    async def log_bulk_message_delete(self, messages: List[discord.Message]):
        """Логирование массового удаления сообщений"""
        if not messages:
            return
            
        channel = messages[0].channel
        count = len(messages)
        
        fields = [
            {"name": f"{Emojis.DOT} Канал", "value": channel.mention, "inline": True},
            {"name": f"{Emojis.DOT} Количество", "value": str(count), "inline": True}
        ]
        
        # Добавляем информацию о последних 5 сообщениях
        last_messages = sorted(messages, key=lambda m: m.created_at, reverse=True)[:5]
        for msg in last_messages:
            if not msg.author.bot:
                content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                fields.append({
                    "name": f"{Emojis.DOT} Сообщение от {msg.author.name}",
                    "value": content or "*пусто*",
                    "inline": False
                })
        
        await self.log_event(
            title=f"{Emojis.ERROR} Массовое удаление сообщений",
            description=f"Удалено {count} сообщений в канале {channel.mention}",
            color='RED',
            fields=fields
        ) 