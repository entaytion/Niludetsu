from ..utils.logging import BaseLogger
from ..utils.constants import Emojis
import discord
from typing import Optional
from discord.utils import format_dt

class StageLogger(BaseLogger):
    """Логгер для стейдж-каналов Discord."""
    
    async def log_stage_start(self, stage: discord.StageInstance):
        """Логирование начала стейдж-события"""
        fields = [
            {"name": f"{Emojis.DOT} Название", "value": stage.topic, "inline": True},
            {"name": f"{Emojis.DOT} Канал", "value": stage.channel.mention, "inline": True},
            {"name": f"{Emojis.DOT} Приватность", "value": self._get_privacy_level(stage.privacy_level), "inline": True},
            {"name": f"{Emojis.DOT} Создатель", "value": stage.creator.mention if stage.creator else "Неизвестно", "inline": True},
            {"name": f"{Emojis.DOT} Время начала", "value": format_dt(stage.created_at), "inline": True}
        ]
        
        await self.log_event(
            title=f"{Emojis.SUCCESS} Начато стейдж-событие",
            description=f"В канале {stage.channel.mention} начато новое стейдж-событие",
            color='GREEN',
            fields=fields
        )
        
    async def log_stage_end(self, stage: discord.StageInstance):
        """Логирование завершения стейдж-события"""
        duration = discord.utils.utcnow() - stage.created_at
        hours, remainder = divmod(int(duration.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        duration_str = f"{hours}ч {minutes}м {seconds}с" if hours else f"{minutes}м {seconds}с"
        
        fields = [
            {"name": f"{Emojis.DOT} Название", "value": stage.topic, "inline": True},
            {"name": f"{Emojis.DOT} Канал", "value": stage.channel.mention, "inline": True},
            {"name": f"{Emojis.DOT} Создатель", "value": stage.creator.mention if stage.creator else "Неизвестно", "inline": True},
            {"name": f"{Emojis.DOT} Время начала", "value": format_dt(stage.created_at), "inline": True},
            {"name": f"{Emojis.DOT} Длительность", "value": duration_str, "inline": True}
        ]
        
        await self.log_event(
            title=f"{Emojis.INFO} Завершено стейдж-событие",
            description=f"В канале {stage.channel.mention} завершено стейдж-событие",
            color='BLUE',
            fields=fields
        )
        
    async def log_stage_topic_update(self, before: discord.StageInstance, after: discord.StageInstance):
        """Логирование изменения темы стейдж-события"""
        fields = [
            {"name": f"{Emojis.DOT} Канал", "value": after.channel.mention, "inline": True},
            {"name": f"{Emojis.DOT} Старая тема", "value": before.topic, "inline": True},
            {"name": f"{Emojis.DOT} Новая тема", "value": after.topic, "inline": True}
        ]
        
        await self.log_event(
            title=f"{Emojis.INFO} Изменена тема стейдж-события",
            description=f"Обновлена тема стейдж-события в канале {after.channel.mention}",
            color='BLUE',
            fields=fields
        )
        
    async def log_stage_privacy_update(self, before: discord.StageInstance, after: discord.StageInstance):
        """Логирование изменения приватности стейдж-события"""
        fields = [
            {"name": f"{Emojis.DOT} Канал", "value": after.channel.mention, "inline": True},
            {"name": f"{Emojis.DOT} Старый уровень", "value": self._get_privacy_level(before.privacy_level), "inline": True},
            {"name": f"{Emojis.DOT} Новый уровень", "value": self._get_privacy_level(after.privacy_level), "inline": True}
        ]
        
        await self.log_event(
            title=f"{Emojis.INFO} Изменена приватность стейдж-события",
            description=f"Обновлен уровень приватности стейдж-события в канале {after.channel.mention}",
            color='BLUE',
            fields=fields
        )
        
    def _get_privacy_level(self, level: discord.StagePrivacyLevel) -> str:
        """Получение читаемого названия уровня приватности"""
        return {
            discord.StagePrivacyLevel.public: "Публичный",
            discord.StagePrivacyLevel.guild_only: "Только для сервера",
            discord.StagePrivacyLevel.closed: "Закрытый"
        }.get(level, "Неизвестно") 