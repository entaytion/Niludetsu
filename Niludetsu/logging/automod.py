from Niludetsu import BaseLogger, Emojis, LoggingState
import discord
from typing import List, Dict, Any

class AutoModLogger(BaseLogger):
    """Логгер для событий AutoMod Discord."""
    
    def __init__(self, bot: discord.Client):
        super().__init__(bot)
        self.log_channel = None
        bot.loop.create_task(self._initialize())
    
    async def _initialize(self):
        """Инициализация логгера"""
        await self.bot.wait_until_ready()
        await self.initialize_logs()
        self.log_channel = LoggingState.log_channel
    
    def _format_rule_info(self, rule: discord.AutoModRule) -> List[Dict[str, Any]]:
        """Форматирует информацию о правиле AutoMod в поля для эмбеда"""
        fields = [
            {"name": f"{Emojis.DOT} ID", "value": str(rule.id), "inline": True},
            {"name": f"{Emojis.DOT} Название", "value": rule.name, "inline": True},
            {"name": f"{Emojis.DOT} Создатель", "value": str(rule.creator), "inline": True},
            {"name": f"{Emojis.DOT} Триггер", "value": str(rule.trigger_type), "inline": True},
            {"name": f"{Emojis.DOT} Действие", "value": str(rule.actions[0].type if rule.actions else "Нет"), "inline": True},
            {"name": f"{Emojis.DOT} Включено", "value": "Да" if rule.enabled else "Нет", "inline": True}
        ]
        
        if rule.exempt_roles:
            fields.append({
                "name": f"{Emojis.DOT} Исключенные роли",
                "value": ", ".join([f"<@&{role_id}>" for role_id in rule.exempt_roles]),
                "inline": False
            })
            
        if rule.exempt_channels:
            fields.append({
                "name": f"{Emojis.DOT} Исключенные каналы",
                "value": ", ".join([f"<#{channel_id}>" for channel_id in rule.exempt_channels]),
                "inline": False
            })
            
        return fields
    
    async def log_automod_rule_create(self, rule: discord.AutoModRule):
        """Логирование создания правила AutoMod"""
        fields = self._format_rule_info(rule)
        
        await self.log_event(
            title=f"{Emojis.SUCCESS} Новое правило AutoMod",
            description=f"Создано новое правило AutoMod: `{rule.name}`",
            color="GREEN",
            fields=fields
        )
        
    async def log_automod_rule_update(self, rule: discord.AutoModRule):
        """Логирование обновления правила AutoMod"""
        fields = self._format_rule_info(rule)
        
        await self.log_event(
            title=f"{Emojis.INFO} Обновление правила AutoMod",
            description=f"Правило AutoMod `{rule.name}` было обновлено",
            color="BLUE",
            fields=fields
        )
        
    async def log_automod_rule_delete(self, rule: discord.AutoModRule):
        """Логирование удаления правила AutoMod"""
        fields = self._format_rule_info(rule)
        
        await self.log_event(
            title=f"{Emojis.ERROR} Правило AutoMod удалено",
            description=f"Правило AutoMod `{rule.name}` было удалено",
            color="RED",
            fields=fields
        )
        
    async def log_automod_action(self, action: discord.AutoModAction, message: discord.Message = None):
        """Логирование действия AutoMod"""
        fields = [
            {"name": f"{Emojis.DOT} Правило", "value": str(action.rule_id), "inline": True},
            {"name": f"{Emojis.DOT} Действие", "value": str(action.type), "inline": True}
        ]
        
        if message:
            fields.extend([
                {"name": f"{Emojis.DOT} Пользователь", "value": message.author.mention, "inline": True},
                {"name": f"{Emojis.DOT} Канал", "value": message.channel.mention, "inline": True},
                {"name": f"{Emojis.DOT} Сообщение", "value": message.content[:1000] + "..." if len(message.content) > 1000 else message.content, "inline": False}
            ])
        
        await self.log_event(
            title=f"{Emojis.WARNING} Действие AutoMod",
            description="AutoMod применил действие к сообщению",
            color="YELLOW",
            fields=fields
        ) 