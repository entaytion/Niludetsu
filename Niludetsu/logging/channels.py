from ..utils.logging import BaseLogger
from ..utils.constants import Emojis
import discord
from typing import Optional, Union
from discord.channel import TextChannel, VoiceChannel, CategoryChannel, ForumChannel

class ChannelLogger(BaseLogger):
    """Логгер для событий, связанных с каналами Discord."""
    
    async def log_channel_update(self, before: Union[discord.TextChannel, discord.VoiceChannel, discord.CategoryChannel], 
                                after: Union[discord.TextChannel, discord.VoiceChannel, discord.CategoryChannel]):
        """Логирование изменений канала"""
        try:
            changes = []
            
            # Проверяем изменения прав доступа для всех типов каналов
            before_overwrites = {(k.id, tuple(sorted(v))) for k, v in before.overwrites.items()}
            after_overwrites = {(k.id, tuple(sorted(v))) for k, v in after.overwrites.items()}
            
            if before_overwrites != after_overwrites:
                # Находим добавленные и удаленные права
                removed = before_overwrites - after_overwrites
                added = after_overwrites - before_overwrites
                
                for target_id, _ in removed:
                    target = before.guild.get_role(target_id) or before.guild.get_member(target_id)
                    if target:
                        changes.append(f"Удалены права для {target.mention}")
                        
                for target_id, perms in added:
                    target = after.guild.get_role(target_id) or after.guild.get_member(target_id)
                    if target:
                        changes.append(f"Добавлены права для {target.mention}")
                        
                # Находим измененные права
                common_targets = before_overwrites.intersection(after_overwrites)
                for target_id, before_perms in before_overwrites:
                    if (target_id, before_perms) in common_targets:
                        after_perms = next(p for t, p in after_overwrites if t == target_id)
                        if before_perms != after_perms:
                            target = after.guild.get_role(target_id) or after.guild.get_member(target_id)
                            if target:
                                changes.append(f"Изменены права для {target.mention}")
            
            # Остальные проверки для разных типов каналов
            if isinstance(before, discord.TextChannel) and isinstance(after, discord.TextChannel):
                if before.name != after.name:
                    changes.append(f"Название: {before.name} ➜ {after.name}")
                if before.topic != after.topic:
                    changes.append(f"Описание: {before.topic} ➜ {after.topic}")
                if before.nsfw != after.nsfw:
                    changes.append(f"NSFW: {'Да' if before.nsfw else 'Нет'} ➜ {'Да' if after.nsfw else 'Нет'}")
                if before.slowmode_delay != after.slowmode_delay:
                    changes.append(f"Медленный режим: {before.slowmode_delay}с ➜ {after.slowmode_delay}с")
                if before.category != after.category:
                    before_category = before.category.name if before.category else "Нет"
                    after_category = after.category.name if after.category else "Нет"
                    changes.append(f"Категория: {before_category} ➜ {after_category}")
                if before.position != after.position:
                    changes.append(f"Позиция: {before.position} ➜ {after.position}")
                    
            elif isinstance(before, discord.VoiceChannel) and isinstance(after, discord.VoiceChannel):
                if before.name != after.name:
                    changes.append(f"Название: {before.name} ➜ {after.name}")
                if before.bitrate != after.bitrate:
                    changes.append(f"Битрейт: {before.bitrate//1000}kbps ➜ {after.bitrate//1000}kbps")
                if before.user_limit != after.user_limit:
                    changes.append(f"Лимит пользователей: {before.user_limit or 'Без лимита'} ➜ {after.user_limit or 'Без лимита'}")
                if before.rtc_region != after.rtc_region:
                    changes.append(f"Регион: {before.rtc_region or 'Авто'} ➜ {after.rtc_region or 'Авто'}")
                if before.category != after.category:
                    before_category = before.category.name if before.category else "Нет"
                    after_category = after.category.name if after.category else "Нет"
                    changes.append(f"Категория: {before_category} ➜ {after_category}")
                if before.position != after.position:
                    changes.append(f"Позиция: {before.position} ➜ {after.position}")
                    
            elif isinstance(before, discord.ForumChannel) and isinstance(after, discord.ForumChannel):
                if before.name != after.name:
                    changes.append(f"Название: {before.name} ➜ {after.name}")
                if before.available_tags != after.available_tags:
                    old_tags = ", ".join([tag.name for tag in before.available_tags]) or "Нет тегов"
                    new_tags = ", ".join([tag.name for tag in after.available_tags]) or "Нет тегов"
                    changes.append(f"Теги: {old_tags} ➜ {new_tags}")
                if before.category != after.category:
                    before_category = before.category.name if before.category else "Нет"
                    after_category = after.category.name if after.category else "Нет"
                    changes.append(f"Категория: {before_category} ➜ {after_category}")
                if before.position != after.position:
                    changes.append(f"Позиция: {before.position} ➜ {after.position}")

            elif isinstance(before, discord.CategoryChannel) and isinstance(after, discord.CategoryChannel):
                if before.name != after.name:
                    changes.append(f"Название: {before.name} ➜ {after.name}")
                if before.position != after.position:
                    changes.append(f"Позиция: {before.position} ➜ {after.position}")
                    
            if changes:
                channel_type = "Категория" if isinstance(after, discord.CategoryChannel) else "Канал"
                mention = after.mention if hasattr(after, 'mention') else f"#{after.name}"
                
                await self.log_event(
                    title=f"{Emojis.INFO} Изменен {channel_type.lower()}",
                    description=f"{channel_type} {mention} был изменен\n" + "\n".join(changes),
                    color='BLUE',
                    event_type="channel_update",
                    fields=[
                        {"name": f"{Emojis.DOT} ID", "value": str(after.id), "inline": True},
                        {"name": f"{Emojis.DOT} Тип", "value": str(after.type).replace('_', ' ').title(), "inline": True}
                    ]
                )
                
        except Exception as e:
            print(f"Ошибка при логировании изменения канала: {e}")
        
    async def log_channel_create(self, channel: discord.abc.GuildChannel):
        """Логирование создания канала"""
        channel_type = str(channel.type).replace('_', ' ').title()
        
        fields = [
            {"name": f"{Emojis.DOT} Название", "value": channel.name, "inline": True},
            {"name": f"{Emojis.DOT} ID", "value": str(channel.id), "inline": True},
            {"name": f"{Emojis.DOT} Тип", "value": channel_type, "inline": True},
            {"name": f"{Emojis.DOT} Категория", "value": channel.category.name if channel.category else "Нет", "inline": True}
        ]
        
        await self.log_event(
            title=f"{Emojis.SUCCESS} Создан новый канал",
            description=f"Создан канал {channel.mention}",
            color='GREEN',
            fields=fields,
            event_type="channel_create"
        )
        
    async def log_channel_delete(self, channel: discord.abc.GuildChannel):
        """Логирование удаления канала"""
        channel_type = str(channel.type).replace('_', ' ').title()
        
        fields = [
            {"name": f"{Emojis.DOT} Название", "value": channel.name, "inline": True},
            {"name": f"{Emojis.DOT} ID", "value": str(channel.id), "inline": True},
            {"name": f"{Emojis.DOT} Тип", "value": channel_type, "inline": True},
            {"name": f"{Emojis.DOT} Категория", "value": channel.category.name if channel.category else "Нет", "inline": True}
        ]
        
        await self.log_event(
            title=f"{Emojis.ERROR} Канал удален",
            description=f"Удален канал #{channel.name}",
            color='RED',
            fields=fields,
            event_type="channel_delete"
        )
        
    async def log_channel_pins_update(self, channel: discord.TextChannel, last_pin):
        """Логирование обновления закрепленных сообщений"""
        await self.log_event(
            title=f"{Emojis.INFO} Обновлены закрепленные сообщения",
            description=f"В канале {channel.mention} обновлены закрепленные сообщения",
            color='BLUE',
            fields=[
                {"name": f"{Emojis.DOT} Канал", "value": channel.mention, "inline": True},
                {"name": f"{Emojis.DOT} Последнее закрепление", "value": last_pin.strftime("%d.%m.%Y %H:%M:%S") if last_pin else "Нет закрепленных", "inline": True}
            ],
            event_type="channel_pins_update"
        )
        
    async def log_channel_nsfw_update(self, before: discord.TextChannel, after: discord.TextChannel):
        """Логирование изменения NSFW статуса канала"""
        fields = [
            {"name": f"{Emojis.DOT} Канал", "value": after.mention, "inline": True},
            {"name": f"{Emojis.DOT} ID", "value": str(after.id), "inline": True},
            {"name": f"{Emojis.DOT} Старый статус", "value": "18+" if before.nsfw else "Обычный", "inline": True},
            {"name": f"{Emojis.DOT} Новый статус", "value": "18+" if after.nsfw else "Обычный", "inline": True}
        ]
        
        await self.log_event(
            title=f"{Emojis.INFO} Изменен NSFW статус канала",
            description=f"Обновлен статус ограничения канала {after.mention}",
            color='BLUE',
            fields=fields
        )
        
    async def log_channel_parent_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        """Логирование изменения родительской категории"""
        await self.log_channel_update(before, after)
        
    async def log_channel_permissions_update(self, channel: discord.abc.GuildChannel, target: Union[discord.Role, discord.Member], before: discord.Permissions, after: discord.Permissions):
        """Логирование изменения прав доступа"""
        changes = []
        for perm, value in after:
            if getattr(before, perm) != value:
                changes.append(f"{perm}: {'✅' if value else '❌'}")
                
        if changes:
            fields = [
                {"name": f"{Emojis.DOT} Канал", "value": channel.mention, "inline": True},
                {"name": f"{Emojis.DOT} Цель", "value": target.mention, "inline": True},
                {"name": f"{Emojis.DOT} Изменения", "value": "\n".join(changes), "inline": False}
            ]
            
            await self.log_event(
                title=f"{Emojis.INFO} Изменены права доступа",
                description=f"В канале {channel.mention} изменены права для {target.mention}",
                color='BLUE',
                fields=fields
            )
            
    async def log_channel_type_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        """Логирование изменения типа канала"""
        await self.log_channel_update(before, after)
        
    async def log_voice_channel_update(self, before: VoiceChannel, after: VoiceChannel, change_type: str, old_value: any, new_value: any):
        """Логирование изменений голосового канала"""
        await self.log_channel_update(before, after)
        
    async def log_channel_bitrate_update(self, before: VoiceChannel, after: VoiceChannel):
        """Логирование изменения битрейта"""
        await self.log_voice_channel_update(before, after, "Битрейт", f"{before.bitrate//1000}kbps", f"{after.bitrate//1000}kbps")
        
    async def log_channel_user_limit_update(self, before: VoiceChannel, after: VoiceChannel):
        """Логирование изменения лимита пользователей"""
        await self.log_voice_channel_update(before, after, "Лимит пользователей", 
                                          before.user_limit or "Без лимита", 
                                          after.user_limit or "Без лимита")
        
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
        
    async def log_forum_channel_update(self, before: ForumChannel, after: ForumChannel, change_type: str, old_value: any, new_value: any):
        """Логирование изменений форум-канала"""
        await self.log_channel_update(before, after)
        
    async def log_channel_default_archive_update(self, before: TextChannel, after: TextChannel):
        """Логирование изменения времени архивации по умолчанию"""
        await self.log_channel_update(before, after)
        
    async def log_channel_default_thread_slowmode_update(self, before: TextChannel, after: TextChannel):
        """Логирование изменения медленного режима тредов по умолчанию"""
        await self.log_channel_update(before, after)
        
    async def log_forum_tags_update(self, before: ForumChannel, after: ForumChannel):
        """Логирование изменения тегов форума"""
        old_tags = ", ".join([tag.name for tag in before.available_tags]) or "Нет тегов"
        new_tags = ", ".join([tag.name for tag in after.available_tags]) or "Нет тегов"
        await self.log_forum_channel_update(before, after, "Теги", old_tags, new_tags)
        
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
            title = f"{Emojis.SUCCESS} Участник присоединился к голосовому каналу"
            color = 'GREEN'
        elif before and not after:  # Покинул
            description = f"{member.mention} покинул {before.mention}"
            title = f"{Emojis.ERROR} Участник покинул голосовой канал"
            color = 'RED'
        else:  # Перешел
            description = f"{member.mention} перешел из {before.mention} в {after.mention}"
            title = f"{Emojis.INFO} Участник сменил голосовой канал"
            color = 'BLUE'
            
        fields = [
            {"name": f"{Emojis.DOT} Участник", "value": f"{member} ({member.id})", "inline": True},
            {"name": f"{Emojis.DOT} Канал до", "value": before.mention if before else "Нет", "inline": True},
            {"name": f"{Emojis.DOT} Канал после", "value": after.mention if after else "Нет", "inline": True}
        ]
        
        await self.log_event(
            title=title,
            description=description,
            color=color,
            fields=fields,
            event_type="voice_update"
        ) 