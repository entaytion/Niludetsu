from Niludetsu import BaseLogger, Emojis, LoggingState
import discord
from typing import Optional
import traceback
from datetime import datetime

class VoiceLogger(BaseLogger):
    """Логгер для голосовых каналов Discord."""
    
    def __init__(self, bot: discord.Client):
        super().__init__(bot)
        self.log_channel = None
        self._ready = False
        self.bot.loop.create_task(self._initialize())
    
    async def _initialize(self):
        """Инициализация логгера"""
        try:
            await self.bot.wait_until_ready()
            self.log_channel = LoggingState.log_channel
            self._ready = True
        except Exception as e:
            print(f"❌ Ошибка инициализации логов: {e}")
            traceback.print_exc()
    
    async def log_voice_channel_full(self, channel: discord.VoiceChannel):
        """Логирование заполнения голосового канала"""
        if not self._ready or not self.log_channel:
            return
            
        try:
            fields = [
                {"name": f"{Emojis.DOT} Канал", "value": channel.mention, "inline": True},
                {"name": f"{Emojis.DOT} ID", "value": str(channel.id), "inline": True},
                {"name": f"{Emojis.DOT} Лимит", "value": str(channel.user_limit), "inline": True},
                {"name": f"{Emojis.DOT} Категория", "value": channel.category.name if channel.category else "Нет", "inline": True}
            ]
            
            await self.log_event(
                title=f"{Emojis.INFO} Голосовой канал заполнен",
                description=f"Голосовой канал достиг максимального количества участников",
                color='BLUE',
                fields=fields
            )
        except Exception as e:
            print(f"❌ Ошибка логирования заполнения канала: {e}")
    
    async def log_voice_user_join(self, member: discord.Member, channel: discord.VoiceChannel):
        """Логирование присоединения пользователя к голосовому каналу"""
        if not self._ready or not self.log_channel:
            return
            
        try:
            fields = [
                {"name": f"{Emojis.DOT} Пользователь", "value": member.mention, "inline": True},
                {"name": f"{Emojis.DOT} ID пользователя", "value": str(member.id), "inline": True},
                {"name": f"{Emojis.DOT} Канал", "value": channel.mention, "inline": True},
                {"name": f"{Emojis.DOT} Участников", "value": f"{len(channel.members)}/{channel.user_limit if channel.user_limit else '∞'}", "inline": True}
            ]
            
            await self.log_event(
                title=f"{Emojis.SUCCESS} Вход в голосовой канал",
                description=f"{member.mention} присоединился к каналу {channel.mention}",
                color='GREEN',
                fields=fields,
                thumbnail_url=member.display_avatar.url
            )
        except Exception as e:
            print(f"❌ Ошибка логирования входа в канал: {e}")
    
    async def log_voice_user_leave(self, member: discord.Member, channel: discord.VoiceChannel):
        """Логирование выхода пользователя из голосового канала"""
        if not self._ready or not self.log_channel:
            return
            
        try:
            fields = [
                {"name": f"{Emojis.DOT} Пользователь", "value": member.mention, "inline": True},
                {"name": f"{Emojis.DOT} ID пользователя", "value": str(member.id), "inline": True},
                {"name": f"{Emojis.DOT} Канал", "value": channel.mention, "inline": True},
                {"name": f"{Emojis.DOT} Участников", "value": f"{len(channel.members)}/{channel.user_limit if channel.user_limit else '∞'}", "inline": True}
            ]
            
            await self.log_event(
                title=f"{Emojis.ERROR} Выход из голосового канала",
                description=f"{member.mention} покинул канал {channel.mention}",
                color='RED',
                fields=fields,
                thumbnail_url=member.display_avatar.url
            )
        except Exception as e:
            print(f"❌ Ошибка логирования выхода из канала: {e}")

    async def log_voice_status_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Логирование изменений голосового состояния"""
        if not self._ready or not self.log_channel:
            return
            
        try:
            # Подключение к каналу
            if not before.channel and after.channel:
                await self.log_event(
                    title=f"{Emojis.SUCCESS} Вход в голосовой канал",
                    description=f"{member.mention} присоединился к каналу {after.channel.mention}",
                    color='GREEN',
                    fields=[
                        {"name": f"{Emojis.DOT} Пользователь", "value": member.mention, "inline": True},
                        {"name": f"{Emojis.DOT} ID пользователя", "value": str(member.id), "inline": True},
                        {"name": f"{Emojis.DOT} Канал", "value": after.channel.mention, "inline": True},
                        {"name": f"{Emojis.DOT} Участников", "value": f"{len(after.channel.members)}/{after.channel.user_limit if after.channel.user_limit else '∞'}", "inline": True}
                    ],
                    thumbnail_url=member.display_avatar.url
                )

            # Отключение от канала
            elif before.channel and not after.channel:
                await self.log_event(
                    title=f"{Emojis.ERROR} Выход из голосового канала",
                    description=f"{member.mention} покинул канал {before.channel.mention}",
                    color='RED',
                    fields=[
                        {"name": f"{Emojis.DOT} Пользователь", "value": member.mention, "inline": True},
                        {"name": f"{Emojis.DOT} ID пользователя", "value": str(member.id), "inline": True},
                        {"name": f"{Emojis.DOT} Канал", "value": before.channel.mention, "inline": True},
                        {"name": f"{Emojis.DOT} Участников", "value": f"{len(before.channel.members)}/{before.channel.user_limit if before.channel.user_limit else '∞'}", "inline": True}
                    ],
                    thumbnail_url=member.display_avatar.url
                )

            # Переход между каналами
            elif before.channel and after.channel and before.channel != after.channel:
                await self.log_event(
                    title=f"{Emojis.INFO} Смена голосового канала",
                    description=f"{member.mention} перешел из канала {before.channel.mention} в канал {after.channel.mention}",
                    color='BLUE',
                    fields=[
                        {"name": f"{Emojis.DOT} Пользователь", "value": member.mention, "inline": True},
                        {"name": f"{Emojis.DOT} ID пользователя", "value": str(member.id), "inline": True},
                        {"name": f"{Emojis.DOT} Предыдущий канал", "value": before.channel.mention, "inline": True},
                        {"name": f"{Emojis.DOT} Новый канал", "value": after.channel.mention, "inline": True},
                        {"name": f"{Emojis.DOT} Участников", "value": f"{len(after.channel.members)}/{after.channel.user_limit if after.channel.user_limit else '∞'}", "inline": True}
                    ],
                    thumbnail_url=member.display_avatar.url
                )

            # Изменение состояния микрофона
            if before.self_mute != after.self_mute:
                status = "включил" if not after.self_mute else "выключил"
                await self.log_event(
                    title=f"{Emojis.INFO} Изменение состояния микрофона",
                    description=f"{member.mention} {status} микрофон в канале {after.channel.mention}",
                    color='YELLOW',
                    fields=[
                        {"name": f"{Emojis.DOT} Пользователь", "value": member.mention, "inline": True},
                        {"name": f"{Emojis.DOT} ID пользователя", "value": str(member.id), "inline": True},
                        {"name": f"{Emojis.DOT} Канал", "value": after.channel.mention, "inline": True},
                        {"name": f"{Emojis.DOT} Действие", "value": f"Микрофон {status}", "inline": True}
                    ],
                    thumbnail_url=member.display_avatar.url
                )

            # Изменение состояния наушников
            if before.self_deaf != after.self_deaf:
                status = "включил" if not after.self_deaf else "выключил"
                await self.log_event(
                    title=f"{Emojis.INFO} Изменение состояния наушников",
                    description=f"{member.mention} {status} звук в канале {after.channel.mention}",
                    color='YELLOW',
                    fields=[
                        {"name": f"{Emojis.DOT} Пользователь", "value": member.mention, "inline": True},
                        {"name": f"{Emojis.DOT} ID пользователя", "value": str(member.id), "inline": True},
                        {"name": f"{Emojis.DOT} Канал", "value": after.channel.mention, "inline": True},
                        {"name": f"{Emojis.DOT} Действие", "value": f"Звук {status}", "inline": True}
                    ],
                    thumbnail_url=member.display_avatar.url
                )
        except Exception as e:
            print(f"❌ Ошибка при логировании голосового события: {e}")
            traceback.print_exc() 