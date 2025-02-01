"""
Модуль для работы с эмбедами Discord
"""

from typing import Optional, Union, List
import discord
from datetime import datetime
from .constants import Colors, Emojis

# Цвета по умолчанию
COLORS = {
    'DEFAULT': 0xf20c3c,
    'GREEN': 0x30f20c,
    'YELLOW': 0xf1f20c,
    'RED': 0xf20c3c,
    'BLUE': 0x0c3ef2,
    'WHITE': 0xFFFFFF,
    'BLACK': 0x000000
}

class Embed(discord.Embed):
    """
    Утилита для создания красивых эмбедов с предустановленными стилями
    """
    
    def __init__(
        self,
        title: str = None,
        description: str = None,
        color: Union[int, str] = Colors.PRIMARY,
        fields: Optional[List[dict]] = None,
        footer: Optional[dict] = None,
        image_url: Optional[str] = None,
        author: Optional[dict] = None,
        url: Optional[str] = None,
        timestamp: Optional[bool] = None,
        thumbnail_url: Optional[str] = None,
        **kwargs
    ):
        """Инициализация эмбеда"""
        # Если цвет передан как строка, конвертируем его
        if isinstance(color, str):
            color = getattr(Colors, color.upper(), Colors.PRIMARY)
            
        # Инициализируем родительский класс
        super().__init__(
            title=title,
            description=description,
            color=color,
            url=url,
            timestamp=datetime.utcnow() if timestamp else None,
            **kwargs
        )
        
        # Добавляем дополнительные поля
        if fields:
            for field in fields:
                self.add_field(**field)
                
        if footer:
            self.set_footer(**footer)
            
        if thumbnail_url:
            self.set_thumbnail(url=thumbnail_url)
            
        if image_url:
            self.set_image(url=image_url)
            
        if author:
            self.set_author(**author)
    
    @staticmethod
    def default(
        title: str = None,
        description: str = None,
        color: int = Colors.PRIMARY,
        fields: Optional[List[dict]] = None,
        footer: Optional[dict] = None,
        image_url: Optional[str] = None,
        author: Optional[dict] = None,
        url: Optional[str] = None,
        timestamp: Optional[bool] = None,
        thumbnail_url: Optional[str] = None,
        **kwargs
    ) -> discord.Embed:
        """Создает стандартный эмбед с заданными параметрами"""
        return Embed(
            title=title,
            description=description,
            color=color,
            fields=fields,
            footer=footer,
            image_url=image_url,
            author=author,
            url=url,
            timestamp=timestamp,
            thumbnail_url=thumbnail_url,
            **kwargs
        )
    
    @staticmethod
    def success(
        title: str = "Успешно!",
        description: str = None,
        fields: Optional[List[dict]] = None,
        footer: Optional[dict] = None,
        image_url: Optional[str] = None,
        author: Optional[dict] = None,
        url: Optional[str] = None,
        timestamp: Optional[bool] = None,
        thumbnail_url: Optional[str] = None,
        **kwargs
    ) -> discord.Embed:
        """Создает эмбед успешного действия"""
        return Embed(
            title=f"{Emojis.SUCCESS} {title}",
            description=description,
            color=Colors.SUCCESS,
            fields=fields,
            footer=footer,
            image_url=image_url,
            author=author,
            url=url,
            timestamp=timestamp,
            thumbnail_url=thumbnail_url,
            **kwargs
        )
    
    @staticmethod
    def error(
        title: str = "Ошибка!",
        description: str = None,
        fields: Optional[List[dict]] = None,
        footer: Optional[dict] = None,
        image_url: Optional[str] = None,
        author: Optional[dict] = None,
        url: Optional[str] = None,
        timestamp: Optional[bool] = None,
        thumbnail_url: Optional[str] = None,
        **kwargs
    ) -> discord.Embed:
        """Создает эмбед ошибки"""
        return Embed(
            title=f"{Emojis.ERROR} {title}",
            description=description,
            color=Colors.ERROR,
            fields=fields,
            footer=footer,
            image_url=image_url,
            author=author,
            url=url,
            timestamp=timestamp,
            thumbnail_url=thumbnail_url,
            **kwargs
        )
    
    @staticmethod
    def warning(
        title: str = "Предупреждение.",
        description: str = None,
        fields: Optional[List[dict]] = None,
        footer: Optional[dict] = None,
        image_url: Optional[str] = None,
        author: Optional[dict] = None,
        url: Optional[str] = None,
        timestamp: Optional[bool] = None,
        thumbnail_url: Optional[str] = None,
        **kwargs
    ) -> discord.Embed:
        """Создает эмбед предупреждения"""
        return Embed(
            title=f"{Emojis.WARNING} {title}",
            description=description,
            color=Colors.WARNING,
            fields=fields,
            footer=footer,
            image_url=image_url,
            author=author,
            url=url,
            timestamp=timestamp,
            thumbnail_url=thumbnail_url,
            **kwargs
        )
    
    @staticmethod
    def info(
        title: str = "Информация.",
        description: str = None,
        fields: Optional[List[dict]] = None,
        footer: Optional[dict] = None,
        image_url: Optional[str] = None,
        author: Optional[dict] = None,
        url: Optional[str] = None,
        timestamp: Optional[bool] = None,
        thumbnail_url: Optional[str] = None,
        **kwargs
    ) -> discord.Embed:
        """Создает информационный эмбед"""
        return Embed(
            title=f"{Emojis.INFO} {title}",
            description=description,
            color=Colors.INFO,
            fields=fields,
            footer=footer,
            image_url=image_url,
            author=author,
            url=url,
            timestamp=timestamp,
            thumbnail_url=thumbnail_url,
            **kwargs
        )