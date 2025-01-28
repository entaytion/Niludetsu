from ..core.base import BaseLogger, EMOJIS
import discord
from typing import Optional, Union
from discord.channel import TextChannel, VoiceChannel, CategoryChannel, ForumChannel

class ChannelLogger(BaseLogger):
    """Логгер для событий, связанных с каналами Discord."""
    
    async def log_channel_create(self, channel: discord.abc.GuildChannel):
        """Логирование создания канала"""
        channel_type = str(channel.type).replace('_', ' ').title()
        
        fields = [
            {"name": f"{EMOJIS['DOT']} Название", "value": channel.name, "inline": True},
            {"name": f"{EMOJIS['DOT']} ID", "value": str(channel.id), "inline": True},
            {"name": f"{EMOJIS['DOT']} Тип", "value": channel_type, "inline": True},
            {"name": f"{EMOJIS['DOT']} Категория", "value": channel.category.name if channel.category else "Нет", "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['SUCCESS']} Создан новый канал",
            description=f"Создан канал {channel.mention}",
            color='GREEN',
            fields=fields
        )
        
    async def log_channel_delete(self, channel: discord.abc.GuildChannel):
        """Логирование удаления канала"""
        channel_type = str(channel.type).replace('_', ' ').title()
        
        fields = [
            {"name": f"{EMOJIS['DOT']} Название", "value": channel.name, "inline": True},
            {"name": f"{EMOJIS['DOT']} ID", "value": str(channel.id), "inline": True},
            {"name": f"{EMOJIS['DOT']} Тип", "value": channel_type, "inline": True},
            {"name": f"{EMOJIS['DOT']} Категория", "value": channel.category.name if channel.category else "Нет", "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['ERROR']} Канал удален",
            description=f"Удален канал #{channel.name}",
            color='RED',
            fields=fields
        )
        
    async def log_channel_pins_update(self, channel: discord.TextChannel, last_pin):
        """Логирование обновления закрепленных сообщений"""
        await self.log_event(
            title=f"{EMOJIS['INFO']} Обновлены закрепленные сообщения",
            description=f"В канале {channel.mention} обновлены закрепленные сообщения",
            color='BLUE',
            fields=[
                {"name": f"{EMOJIS['DOT']} Канал", "value": channel.mention, "inline": True},
                {"name": f"{EMOJIS['DOT']} Последнее закрепление", "value": last_pin.strftime("%d.%m.%Y %H:%M:%S") if last_pin else "Нет закрепленных", "inline": True}
            ]
        )
        
    async def log_channel_update(self, before: Union[discord.TextChannel, discord.VoiceChannel, discord.CategoryChannel], 
                                after: Union[discord.TextChannel, discord.VoiceChannel, discord.CategoryChannel]):
        """Общий метод для логирования изменений канала"""
        if isinstance(before, discord.TextChannel) and isinstance(after, discord.TextChannel):
            if before.name != after.name:
                await self.log_channel_name_update(before, after)
            if before.topic != after.topic:
                await self.log_channel_topic_update(before, after)
            if before.nsfw != after.nsfw:
                await self.log_channel_nsfw_update(before, after)
            if before.slowmode_delay != after.slowmode_delay:
                await self.log_channel_slowmode_update(before, after)
            if before.category != after.category:
                await self.log_channel_category_update(before, after)
            if before.position != after.position:
                await self.log_channel_position_update(before, after)
        elif isinstance(before, discord.VoiceChannel) and isinstance(after, discord.VoiceChannel):
            if before.name != after.name:
                await self.log_channel_name_update(before, after)
            if before.bitrate != after.bitrate:
                await self.log_channel_bitrate_update(before, after)
            if before.user_limit != after.user_limit:
                await self.log_channel_user_limit_update(before, after)
            if before.category != after.category:
                await self.log_channel_category_update(before, after)
            if before.position != after.position:
                await self.log_channel_position_update(before, after)
            if before.rtc_region != after.rtc_region:
                await self.log_channel_rtc_region_update(before, after)
            if before.video_quality_mode != after.video_quality_mode:
                await self.log_channel_video_quality_update(before, after)
        elif isinstance(before, discord.ForumChannel) and isinstance(after, discord.ForumChannel):
            if before.name != after.name:
                await self.log_channel_name_update(before, after)
            if before.category != after.category:
                await self.log_channel_category_update(before, after)
            if before.position != after.position:
                await self.log_channel_position_update(before, after)
            if before.default_layout != after.default_layout:
                await self.log_forum_layout_update(before, after)
            if before.available_tags != after.available_tags:
                await self.log_forum_tags_update(before, after)
        elif isinstance(before, discord.TextChannel) and isinstance(after, discord.TextChannel):
            if before.default_auto_archive_duration != after.default_auto_archive_duration:
                await self.log_channel_default_archive_update(before, after)
            if before.default_thread_slowmode_delay != after.default_thread_slowmode_delay:
                await self.log_channel_default_thread_slowmode_update(before, after)
        elif isinstance(before, discord.Member) and isinstance(after, discord.VoiceChannel):
            await self.log_voice_status_update(before, before.voice, after)
        
    async def log_channel_name_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        """Логирование изменения имени канала"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Канал", "value": after.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} ID", "value": str(after.id), "inline": True},
            {"name": f"{EMOJIS['DOT']} Старое название", "value": before.name, "inline": True},
            {"name": f"{EMOJIS['DOT']} Новое название", "value": after.name, "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['INFO']} Изменено название канала",
            description=f"Обновлено название канала {after.mention}",
            color='BLUE',
            fields=fields
        )
        
    async def log_channel_topic_update(self, before: TextChannel, after: TextChannel):
        """Логирование изменения темы канала"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Канал", "value": after.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} ID", "value": str(after.id), "inline": True},
            {"name": f"{EMOJIS['DOT']} Старая тема", "value": before.topic or "Нет темы", "inline": False},
            {"name": f"{EMOJIS['DOT']} Новая тема", "value": after.topic or "Нет темы", "inline": False}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['INFO']} Изменена тема канала",
            description=f"Обновлена тема канала {after.mention}",
            color='BLUE',
            fields=fields
        )
        
    async def log_channel_nsfw_update(self, before: discord.TextChannel, after: discord.TextChannel):
        """Логирование изменения NSFW статуса канала"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Канал", "value": after.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} ID", "value": str(after.id), "inline": True},
            {"name": f"{EMOJIS['DOT']} Старый статус", "value": "18+" if before.nsfw else "Обычный", "inline": True},
            {"name": f"{EMOJIS['DOT']} Новый статус", "value": "18+" if after.nsfw else "Обычный", "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['INFO']} Изменен NSFW статус канала",
            description=f"Обновлен статус ограничения канала {after.mention}",
            color='BLUE',
            fields=fields
        )
        
    async def log_channel_category_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        """Логирование изменения категории канала"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Канал", "value": after.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} ID", "value": str(after.id), "inline": True},
            {"name": f"{EMOJIS['DOT']} Старая категория", "value": before.category.name if before.category else "Нет", "inline": True},
            {"name": f"{EMOJIS['DOT']} Новая категория", "value": after.category.name if after.category else "Нет", "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['INFO']} Изменена категория канала",
            description=f"Обновлена категория канала {after.mention}",
            color='BLUE',
            fields=fields
        )
        
    async def log_channel_position_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        """Логирование изменения позиции канала"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Канал", "value": after.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} ID", "value": str(after.id), "inline": True},
            {"name": f"{EMOJIS['DOT']} Старая позиция", "value": str(before.position), "inline": True},
            {"name": f"{EMOJIS['DOT']} Новая позиция", "value": str(after.position), "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['INFO']} Изменена позиция канала",
            description=f"Обновлена позиция канала {after.mention}",
            color='BLUE',
            fields=fields
        )
        
    async def log_channel_slowmode_update(self, before: TextChannel, after: TextChannel):
        """Логирование изменения медленного режима"""
        await self.log_channel_update(before, after)
        
    async def log_channel_rtc_region_update(self, before: VoiceChannel, after: VoiceChannel):
        """Логирование изменения региона RTC"""
        await self.log_voice_channel_update(before, after, "Регион", before.rtc_region or "Авто", after.rtc_region or "Авто")
        
    async def log_channel_video_quality_update(self, before: VoiceChannel, after: VoiceChannel):
        """Логирование изменения качества видео"""
        quality_map = {
            discord.VideoQualityMode.auto: "Авто",
            discord.VideoQualityMode.full: "720p",
        }
        await self.log_voice_channel_update(before, after, "Качество видео", 
                                          quality_map.get(before.video_quality_mode, "Неизвестно"),
                                          quality_map.get(after.video_quality_mode, "Неизвестно"))
        
    async def log_forum_layout_update(self, before: ForumChannel, after: ForumChannel):
        """Логирование изменения макета форума"""
        layout_map = {
            discord.ForumLayoutType.not_set: "Не установлен",
            discord.ForumLayoutType.list_view: "Список",
            discord.ForumLayoutType.gallery_view: "Галерея"
        }
        await self.log_forum_channel_update(before, after, "Макет", 
                                          layout_map.get(before.default_layout, "Неизвестно"),
                                          layout_map.get(after.default_layout, "Неизвестно"))
        
    async def log_voice_status_update(self, member: discord.Member, before: Optional[VoiceChannel], after: Optional[VoiceChannel]):
        """Логирование изменений статуса голосового канала"""
        if not before and after:  # Присоединился
            description = f"{member.mention} присоединился к {after.mention}"
            title = f"{EMOJIS['SUCCESS']} Участник присоединился к голосовому каналу"
            color = 'GREEN'
        elif before and not after:  # Покинул
            description = f"{member.mention} покинул {before.mention}"
            title = f"{EMOJIS['ERROR']} Участник покинул голосовой канал"
            color = 'RED'
        else:  # Перешел
            description = f"{member.mention} перешел из {before.mention} в {after.mention}"
            title = f"{EMOJIS['INFO']} Участник сменил голосовой канал"
            color = 'BLUE'
            
        fields = [
            {"name": f"{EMOJIS['DOT']} Участник", "value": f"{member} ({member.id})", "inline": True},
            {"name": f"{EMOJIS['DOT']} Канал до", "value": before.mention if before else "Нет", "inline": True},
            {"name": f"{EMOJIS['DOT']} Канал после", "value": after.mention if after else "Нет", "inline": True}
        ]
        
        await self.log_event(
            title=title,
            description=description,
            color=color,
            fields=fields
        ) 