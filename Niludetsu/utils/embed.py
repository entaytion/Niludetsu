"""
Модуль для работы с эмбедами Discord
"""

import discord
from typing import Optional, Dict, Any, List, Union

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

def create_embed(
    title: Optional[str] = None,
    description: Optional[str] = None,
    color: Union[str, int] = 'BLUE',
    fields: Optional[List[Dict[str, Any]]] = None,
    footer: Optional[Dict[str, str]] = None,
    image_url: Optional[str] = None,
    author: Optional[Dict[str, str]] = None,
    url: Optional[str] = None,
    timestamp: Optional[bool] = None,
    thumbnail_url: Optional[str] = None
) -> discord.Embed:
    """
    Создает красивый эмбед для Discord с заданными параметрами.
    
    Args:
        title: Заголовок эмбеда
        description: Описание эмбеда
        color: Цвет эмбеда (название или hex-код)
        fields: Список полей эмбеда
        footer: Футер эмбеда (текст и иконка)
        image_url: URL изображения
        author: Информация об авторе
        url: URL для заголовка
        timestamp: Добавить временную метку
        thumbnail_url: URL миниатюры
    
    Returns:
        discord.Embed: Готовый эмбед
    """
    try:
        # Если color это строка, пытаемся получить цвет из COLORS
        if isinstance(color, str):
            color = COLORS.get(color.upper(), COLORS['DEFAULT'])
            
        embed = discord.Embed(
            title=title,
            description=description,
            colour=discord.Colour(color)
        )
        
        if fields:
            for field in fields:
                if not all(key in field for key in ['name', 'value']):
                    continue
                embed.add_field(
                    name=field['name'],
                    value=field['value'], 
                    inline=field.get('inline', False)
                )
                
        if footer:
            if isinstance(footer, dict):
                embed.set_footer(
                    text=footer.get('text', ''),
                    icon_url=footer.get('icon_url', '')
                )
                
        if image_url:
            embed.set_image(url=image_url)
            
        if thumbnail_url:
            embed.set_thumbnail(url=thumbnail_url)
            
        if author and isinstance(author, dict):
            embed.set_author(
                name=author.get('name'),
                icon_url=author.get('icon_url'),
                url=author.get('url')
            )
            
        if url:
            embed.url = url
            
        if timestamp:
            embed.timestamp = discord.utils.utcnow()
            
        return embed
        
    except Exception as e:
        print(f"⚠️ Ошибка при создании эмбеда: {str(e)}")
        return discord.Embed(
            description="Ошибка при создании эмбеда",
            colour=discord.Colour(COLORS['RED'])
        ) 