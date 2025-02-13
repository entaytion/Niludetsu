from Niludetsu import BaseLogger, Emojis, LoggingState
import discord
from typing import List, Dict, Any
from datetime import datetime

class EntitlementLogger(BaseLogger):
    """Логгер для событий подписок (entitlements) Discord."""
    
    def __init__(self, bot: discord.Client):
        super().__init__(bot)
        self.log_channel = None
        bot.loop.create_task(self._initialize())
    
    async def _initialize(self):
        """Инициализация логгера"""
        await self.bot.wait_until_ready()
        await self.initialize_logs()
        self.log_channel = LoggingState.log_channel
        
    def _format_entitlement_info(self, entitlement: discord.Entitlement) -> List[Dict[str, Any]]:
        """Форматирует информацию о подписке в поля для эмбеда"""
        fields = [
            {"name": f"{Emojis.DOT} ID", "value": str(entitlement.id), "inline": True},
            {"name": f"{Emojis.DOT} SKU ID", "value": str(entitlement.sku_id), "inline": True},
            {"name": f"{Emojis.DOT} Тип", "value": str(entitlement.type), "inline": True}
        ]
        
        if entitlement.user:
            fields.append({
                "name": f"{Emojis.DOT} Пользователь",
                "value": f"{entitlement.user.mention} ({entitlement.user})",
                "inline": True
            })
            
        if entitlement.starts_at:
            fields.append({
                "name": f"{Emojis.DOT} Начало подписки",
                "value": discord.utils.format_dt(entitlement.starts_at),
                "inline": True
            })
            
        if entitlement.ends_at:
            fields.append({
                "name": f"{Emojis.DOT} Окончание подписки",
                "value": discord.utils.format_dt(entitlement.ends_at),
                "inline": True
            })
            
        if entitlement.subscription_id:
            fields.append({
                "name": f"{Emojis.DOT} ID подписки",
                "value": str(entitlement.subscription_id),
                "inline": True
            })
            
        return fields
    
    async def log_entitlement_create(self, entitlement: discord.Entitlement):
        """Логирование создания подписки"""
        fields = self._format_entitlement_info(entitlement)
        
        await self.log_event(
            title=f"{Emojis.SUCCESS} Новая подписка",
            description=f"Создана новая подписка для SKU: `{entitlement.sku_id}`",
            color="GREEN",
            fields=fields
        )
        
    async def log_entitlement_update(self, entitlement: discord.Entitlement):
        """Логирование обновления подписки"""
        fields = self._format_entitlement_info(entitlement)
        
        status = "продлена" if entitlement.ends_at and entitlement.ends_at > datetime.utcnow() else "отменена"
        
        await self.log_event(
            title=f"{Emojis.INFO} Обновление подписки",
            description=f"Подписка {status} для SKU: `{entitlement.sku_id}`",
            color="BLUE",
            fields=fields
        )
        
    async def log_entitlement_delete(self, entitlement: discord.Entitlement):
        """Логирование удаления подписки"""
        fields = self._format_entitlement_info(entitlement)
        
        await self.log_event(
            title=f"{Emojis.ERROR} Подписка удалена",
            description=(
                f"Подписка для SKU: `{entitlement.sku_id}` была удалена.\n"
                "Это могло произойти из-за:\n"
                "• Возврата средств Discord\n"
                "• Принудительного удаления подписки"
            ),
            color="RED",
            fields=fields
        ) 