"""
База данных Niludetsu
Модуль для работы с SQLite базой данных, включая управление подключениями,
выполнение запросов и определение схемы таблиц.
"""

from .db import Database
from .tables import (
    Tables,
    TableSchema,
    Column,
    Index
)

__all__ = [
    # Основные классы
    'Database',
    'Tables',
    
    # Вспомогательные классы
    'TableSchema',
    'Column',
    'Index'
] 