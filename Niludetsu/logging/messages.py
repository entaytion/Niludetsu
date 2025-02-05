from ..utils.logging import BaseLogger
from ..utils.constants import Emojis
import discord
from typing import Optional, List, Union
from discord.ext import commands

class MessageLogger(BaseLogger):
    """Логгер для сообщений Discord."""
    
    async def log_message_delete(self, message: discord.Message):
        """Логирование удаления сообщения"""
        # Игнорируем сообщения от ботов
        if message.author.bot:
            return
            
        # Игнорируем пустые сообщения без контента и вложений
        if not message.content and not message.attachments:
            return
            
        fields = [
            {"name": f"{Emojis.DOT} Автор", "value": f"{message.author} ({message.author.mention})", "inline": True},
            {"name": f"{Emojis.DOT} ID автора", "value": str(message.author.id), "inline": True},
        ]
        
        # Добавляем информацию о канале в зависимости от его типа
        if isinstance(message.channel, discord.DMChannel):
            fields.append({"name": f"{Emojis.DOT} Канал", "value": f"Личные сообщения с {message.channel.recipient}", "inline": True})
        else:
            fields.append({"name": f"{Emojis.DOT} Канал", "value": message.channel.mention, "inline": True})
            
        fields.append({"name": f"{Emojis.DOT} ID сообщения", "value": str(message.id), "inline": True})
        
        if message.content:
            fields.append({"name": f"{Emojis.DOT} Содержание", "value": message.content[:1024], "inline": False})
            
        if message.attachments:
            attachments = "\n".join([f"[{a.filename}]({a.url})" for a in message.attachments])
            fields.append({"name": f"{Emojis.DOT} Вложения", "value": attachments, "inline": False})
            
        await self.log_event(
            title=f"{Emojis.ERROR} Сообщение удалено",
            description=f"Удалено сообщение {'в личных сообщениях' if isinstance(message.channel, discord.DMChannel) else f'в канале {message.channel.mention}'}",
            color='RED',
            fields=fields,
            thumbnail_url=message.author.display_avatar.url
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
            
        # Создаем временный файл
        import tempfile
        import os
        
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
        """Логирование редактирования сообщения"""
        # Игнорируем сообщения от ботов
        if before.author.bot:
            return
            
        # Игнорируем если содержимое не изменилось
        if before.content == after.content:
            return
            
        # Базовые поля
        fields = [
            {"name": f"{Emojis.DOT} Автор", "value": f"{after.author} ({after.author.mention})", "inline": True},
            {"name": f"{Emojis.DOT} ID автора", "value": str(after.author.id), "inline": True},
        ]
        
        # Добавляем информацию о канале в зависимости от его типа
        if isinstance(after.channel, discord.DMChannel):
            fields.append({"name": f"{Emojis.DOT} Канал", "value": f"Личные сообщения с {after.channel.recipient}", "inline": True})
        else:
            fields.append({"name": f"{Emojis.DOT} Канал", "value": after.channel.mention, "inline": True})
            
        # Добавляем остальные поля
        fields.extend([
            {"name": f"{Emojis.DOT} ID сообщения", "value": str(after.id), "inline": True},
            {"name": f"{Emojis.DOT} Ссылка", "value": f"[Перейти к сообщению]({after.jump_url})", "inline": True},
            {"name": f"{Emojis.DOT} Старое содержание", "value": before.content[:1024] or "Пусто", "inline": False},
            {"name": f"{Emojis.DOT} Новое содержание", "value": after.content[:1024] or "Пусто", "inline": False}
        ])
        
        await self.log_event(
            title=f"{Emojis.INFO} Сообщение отредактировано",
            description=f"Отредактировано сообщение {'в личных сообщениях' if isinstance(after.channel, discord.DMChannel) else f'в канале {after.channel.mention}'}",
            color='BLUE',
            fields=fields,
            thumbnail_url=after.author.display_avatar.url
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
        try:
            if not messages:
                return
                
            channel = messages[0].channel
            deleted_count = len(messages)
            
            # Фильтруем сообщения от ботов
            user_messages = [msg for msg in messages if not msg.author.bot]
            if not user_messages:
                return
                
            # Создаем список удаленных сообщений
            message_list = []
            for msg in user_messages:
                author = f"{msg.author} ({msg.author.id})"
                content = msg.content if msg.content else "[Нет содержимого]"
                attachments = ""
                
                if msg.attachments:
                    attachments = f" | Вложения: {', '.join([a.filename for a in msg.attachments])}"
                    
                if len(content) > 50:
                    content = content[:47] + "..."
                    
                timestamp = msg.created_at.strftime("%d.%m.%Y %H:%M:%S")
                message_list.append(f"• [{timestamp}] {author}: {content}{attachments}")

            # Ограничиваем количество отображаемых сообщений
            displayed_messages = message_list[:15]
            if len(message_list) > 15:
                displayed_messages.append(f"... и еще {len(message_list) - 15} сообщений")

            fields = [
                {"name": f"{Emojis.DOT} Канал", "value": channel.mention, "inline": True},
                {"name": f"{Emojis.DOT} Всего удалено", "value": str(deleted_count), "inline": True},
                {"name": f"{Emojis.DOT} От пользователей", "value": str(len(user_messages)), "inline": True},
                {"name": f"{Emojis.DOT} Удаленные сообщения", "value": "\n".join(displayed_messages), "inline": False}
            ]

            await self.log_event(
                title=f"{Emojis.ERROR} Массовое удаление сообщений",
                description=f"В канале {channel.mention} было массово удалено {deleted_count} сообщений",
                color='RED',
                fields=fields
            )
            
        except Exception as e:
            print(f"Ошибка при логировании массового удаления сообщений: {e}")
            import traceback
            traceback.print_exc() 