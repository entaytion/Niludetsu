from ..utils.logging import BaseLogger
from ..utils.constants import Emojis
import discord
from typing import Optional, List, Dict, Union
from discord.channel import TextChannel, VoiceChannel, CategoryChannel, ForumChannel
from datetime import datetime

class ChannelLogger(BaseLogger):
    """Логгер для каналов Discord."""
    
    def _get_permission_changes(self, before: Dict[discord.Role, discord.PermissionOverwrite],
                              after: Dict[discord.Role, discord.PermissionOverwrite]) -> List[str]:
        """Получает список изменений прав"""
        changes = []
        
        # Получаем все уникальные роли
        all_roles = set(before.keys()) | set(after.keys())
        
        for role in all_roles:
            before_perms = before.get(role)
            after_perms = after.get(role)
            
            if not before_perms and after_perms:
                # Добавлены новые права
                allowed = [perm[0] for perm in after_perms if perm[1] is True]
                denied = [perm[0] for perm in after_perms if perm[1] is False]
                
                if allowed:
                    changes.append(f"✅ {role.mention}: Разрешено: {', '.join(allowed)}")
                if denied:
                    changes.append(f"❌ {role.mention}: Запрещено: {', '.join(denied)}")
                    
            elif before_perms and not after_perms:
                # Удалены права
                changes.append(f"🗑️ {role.mention}: Права удалены")
                
            elif before_perms and after_perms:
                # Изменены существующие права
                changed_perms = []
                for perm, value in after_perms:
                    before_value = dict(before_perms).get(perm)
                    if before_value != value:
                        status = "✅" if value else "❌"
                        changed_perms.append(f"{status} {perm}")
                        
                if changed_perms:
                    changes.append(f"📝 {role.mention}: {', '.join(changed_perms)}")
        
        return changes
    
    async def log_channel_create(self, channel: discord.abc.GuildChannel):
        """Логирование создания канала"""
        channel_type = {
            discord.TextChannel: "текстовый канал",
            discord.VoiceChannel: "голосовой канал",
            discord.CategoryChannel: "категория",
            discord.StageChannel: "трибуна",
            discord.ForumChannel: "форум"
        }.get(type(channel), "канал")
        
        fields = [
            {"name": f"{Emojis.DOT} Название", "value": channel.name, "inline": True},
            {"name": f"{Emojis.DOT} ID", "value": str(channel.id), "inline": True},
            {"name": f"{Emojis.DOT} Тип", "value": channel_type, "inline": True}
        ]
        
        if isinstance(channel, discord.TextChannel):
            fields.extend([
                {"name": f"{Emojis.DOT} NSFW", "value": "Да" if channel.is_nsfw() else "Нет", "inline": True},
                {"name": f"{Emojis.DOT} Медленный режим", "value": f"{channel.slowmode_delay} сек.", "inline": True}
            ])
            
        if channel.category:
            fields.append({"name": f"{Emojis.DOT} Категория", "value": channel.category.name, "inline": True})
        
        await self.log_event(
            title=f"{Emojis.SUCCESS} Создан новый канал",
            description=f"Создан новый {channel_type} {channel.mention}",
            color='GREEN',
            fields=fields
        )
        
    async def log_channel_delete(self, channel: discord.abc.GuildChannel):
        """Логирование удаления канала"""
        channel_type = {
            discord.TextChannel: "текстовый канал",
            discord.VoiceChannel: "голосовой канал",
            discord.CategoryChannel: "категория",
            discord.StageChannel: "трибуна",
            discord.ForumChannel: "форум"
        }.get(type(channel), "канал")
        
        fields = [
            {"name": f"{Emojis.DOT} Название", "value": channel.name, "inline": True},
            {"name": f"{Emojis.DOT} ID", "value": str(channel.id), "inline": True},
            {"name": f"{Emojis.DOT} Тип", "value": channel_type, "inline": True}
        ]
        
        if channel.category:
            fields.append({"name": f"{Emojis.DOT} Категория", "value": channel.category.name, "inline": True})
        
        await self.log_event(
            title=f"{Emojis.ERROR} Канал удален",
            description=f"Удален {channel_type} {channel.name}",
            color='RED',
            fields=fields
        )
        
    async def log_channel_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        """Логирование изменений канала"""
        changes = []
        fields = [
            {"name": f"{Emojis.DOT} Канал", "value": after.mention, "inline": True},
            {"name": f"{Emojis.DOT} ID", "value": str(after.id), "inline": True}
        ]
        
        # Проверяем изменение названия
        if before.name != after.name:
            changes.append(f"Название: {before.name} ➜ {after.name}")
            
        # Проверяем изменение категории
        if before.category != after.category:
            old_category = before.category.name if before.category else "Нет"
            new_category = after.category.name if after.category else "Нет"
            changes.append(f"Категория: {old_category} ➜ {new_category}")
            
        # Проверяем изменения для текстового канала
        if isinstance(after, discord.TextChannel):
            if before.topic != after.topic:
                changes.append(f"Описание: {before.topic or 'Нет'} ➜ {after.topic or 'Нет'}")
            if before.slowmode_delay != after.slowmode_delay:
                changes.append(f"Медленный режим: {before.slowmode_delay} сек. ➜ {after.slowmode_delay} сек.")
            if before.nsfw != after.nsfw:
                changes.append(f"NSFW: {'Да' if before.nsfw else 'Нет'} ➜ {'Да' if after.nsfw else 'Нет'}")
                
        # Проверяем изменения прав доступа
        permission_changes = self._get_permission_changes(before.overwrites, after.overwrites)
        if permission_changes:
            fields.append({
                "name": f"{Emojis.DOT} Изменения прав",
                "value": "\n".join(permission_changes),
                "inline": False
            })
            
        if changes:
            fields.append({
                "name": f"{Emojis.DOT} Изменения",
                "value": "\n".join(changes),
                "inline": False
            })
            
            await self.log_event(
                title=f"{Emojis.INFO} Канал изменен",
                description=f"Изменены настройки канала {after.mention}",
                color='BLUE',
                fields=fields
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