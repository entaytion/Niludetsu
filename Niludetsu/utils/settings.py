"""
Управление настройками бота
"""
from typing import Optional, Any, Dict
from ..database import Database

class Settings:
    """Класс для работы с настройками бота"""
    
    def __init__(self):
        self.db = Database()
        
    async def get(self, guild_id: str, category: str, key: str) -> Optional[str]:
        """Получить значение настройки"""
        result = await self.db.get_row(
            'settings',
            guild_id=str(guild_id),
            category=category,
            key=key
        )
        return result['value'] if result else None
        
    async def set(self, guild_id: str, category: str, key: str, value: str) -> None:
        """Установить значение настройки"""
        await self.db.insert(
            'settings',
            {
                'guild_id': str(guild_id),
                'category': category,
                'key': key,
                'value': str(value)
            }
        )
        
    async def delete(self, guild_id: str, category: str, key: str) -> None:
        """Удалить настройку"""
        await self.db.delete(
            'settings',
            guild_id=str(guild_id),
            category=category,
            key=key
        )
        
    async def get_all(self, guild_id: str, category: Optional[str] = None) -> Dict[str, Any]:
        """Получить все настройки для сервера"""
        conditions = {'guild_id': str(guild_id)}
        if category:
            conditions['category'] = category
            
        settings = {}
        async for row in await self.db.get_rows('settings', **conditions):
            if row['category'] not in settings:
                settings[row['category']] = {}
            settings[row['category']][row['key']] = row['value']
            
        return settings 