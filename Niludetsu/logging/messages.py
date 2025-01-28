from ..core.base import BaseLogger, EMOJIS
import discord
from typing import Optional, List, Union
from discord.ext import commands

class MessageLogger(BaseLogger):
    """Логгер для сообщений Discord."""
    
    async def log_message_delete(self, message: discord.Message):
        """Логирование удаления сообщения"""
        if not message.content and not message.attachments:
            return
            
        fields = [
            {"name": f"{EMOJIS['DOT']} Автор", "value": message.author.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} Канал", "value": message.channel.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} ID сообщения", "value": str(message.id), "inline": True}
        ]
        
        if message.content:
            fields.append({"name": f"{EMOJIS['DOT']} Содержание", "value": message.content[:1024], "inline": False})
            
        if message.attachments:
            attachments = "\n".join([f"[{a.filename}]({a.url})" for a in message.attachments])
            fields.append({"name": f"{EMOJIS['DOT']} Вложения", "value": attachments, "inline": False})
            
        await self.log_event(
            title=f"{EMOJIS['ERROR']} Сообщение удалено",
            description=f"Удалено сообщение в канале {message.channel.mention}",
            color='RED',
            fields=fields
        )
        
    async def log_message_bulk_delete(self, messages: List[discord.Message], channel: discord.TextChannel):
        """Логирование массового удаления сообщений"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Канал", "value": channel.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} Количество", "value": str(len(messages)), "inline": True}
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
            fields.append({"name": f"{EMOJIS['DOT']} Последние сообщения", "value": "\n".join(content), "inline": False})
            
        if len(messages) > 10:
            fields.append({"name": f"{EMOJIS['DOT']} Примечание", "value": "Показаны только последние 10 сообщений. Полный список в прикрепленном файле.", "inline": False})
            
        # Создаем временный файл
        import tempfile
        import os
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8', suffix='.txt')
        temp_file.write("\n".join(file_content))
        temp_file.close()
        
        file = discord.File(temp_file.name, filename=f"deleted_messages_{channel.name}_{len(messages)}.txt")
        
        await self.log_event(
            title=f"{EMOJIS['ERROR']} Массовое удаление сообщений",
            description=f"Удалено {len(messages)} сообщений в канале {channel.mention}",
            color='RED',
            fields=fields,
            file=file
        )
        
        # Удаляем временный файл
        os.unlink(temp_file.name)
        
    async def log_message_edit(self, before: discord.Message, after: discord.Message):
        """Логирование редактирования сообщения"""
        if before.content == after.content:
            return
            
        fields = [
            {"name": f"{EMOJIS['DOT']} Автор", "value": after.author.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} Канал", "value": after.channel.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} Ссылка", "value": f"[Перейти]({after.jump_url})", "inline": True},
            {"name": f"{EMOJIS['DOT']} Старое содержание", "value": before.content[:1024] or "Пусто", "inline": False},
            {"name": f"{EMOJIS['DOT']} Новое содержание", "value": after.content[:1024] or "Пусто", "inline": False}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['INFO']} Сообщение отредактировано",
            description=f"Отредактировано сообщение в канале {after.channel.mention}",
            color='BLUE',
            fields=fields
        )
        
    async def log_message_publish(self, message: discord.Message):
        """Логирование публикации сообщения в новостном канале"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Автор", "value": message.author.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} Канал", "value": message.channel.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} Ссылка", "value": f"[Перейти]({message.jump_url})", "inline": True}
        ]
        
        if message.content:
            fields.append({"name": f"{EMOJIS['DOT']} Содержание", "value": message.content[:1024], "inline": False})
            
        if message.attachments:
            attachments = "\n".join([f"[{a.filename}]({a.url})" for a in message.attachments])
            fields.append({"name": f"{EMOJIS['DOT']} Вложения", "value": attachments, "inline": False})
            
        await self.log_event(
            title=f"{EMOJIS['SUCCESS']} Сообщение опубликовано",
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
            {"name": f"{EMOJIS['DOT']} Пользователь", "value": user.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} Канал", "value": channel.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} Команда", "value": f"`{command}`", "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['INFO']} Использована команда",
            description=f"Пользователь использовал команду в канале {channel.mention}",
            color='BLUE',
            fields=fields
        ) 