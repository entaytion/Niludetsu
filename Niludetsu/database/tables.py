from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Column:
    """Описание колонки таблицы"""
    type: str
    required: bool = False
    default: str = None
    description: str = None
    
    def __str__(self) -> str:
        """Преобразует описание колонки в SQL"""
        sql = [self.type]
        if self.required:
            sql.append("NOT NULL")
        if self.default is not None:
            sql.append(f"DEFAULT {self.default}")
        return " ".join(sql)

@dataclass
class Index:
    """Описание индекса таблицы"""
    name: str
    columns: List[str]
    unique: bool = False
    
    def __str__(self) -> str:
        """Преобразует описание индекса в SQL"""
        unique = "UNIQUE " if self.unique else ""
        return f"CREATE {unique}INDEX IF NOT EXISTS {self.name} ON {{table}}({', '.join(self.columns)})"

class TableSchema:
    """Базовый класс для схемы таблицы"""
    
    # Общие колонки для всех таблиц
    id = Column("INTEGER PRIMARY KEY AUTOINCREMENT")
    created_at = Column("DATETIME", default="CURRENT_TIMESTAMP", description="Дата создания")
    updated_at = Column("DATETIME", default="CURRENT_TIMESTAMP", description="Дата обновления")

def get_schema(cls) -> Dict:
    """Получает схему всех таблиц"""
    schema = {}
    
    for table_name, table_class in cls.__dict__.items():
        if isinstance(table_class, type) and issubclass(table_class, TableSchema) and table_class != TableSchema:
            columns = {}
            
            # Добавляем колонки из базового класса
            for name, col in TableSchema.__dict__.items():
                if isinstance(col, Column):
                    columns[name] = str(col)
            
            # Добавляем колонки из текущего класса
            for name, col in table_class.__dict__.items():
                if isinstance(col, Column):
                    columns[name] = str(col)
            
            # Добавляем индексы
            if hasattr(table_class, 'INDEXES'):
                columns['INDEXES'] = [
                    str(idx).format(table=table_name.lower())
                    for idx in table_class.INDEXES
                ]
            
            schema[table_name.lower()] = columns
            
    return schema

class Tables:
    """Схемы таблиц базы данных"""
    
    class Users(TableSchema):
        """Таблица пользователей"""
        user_id = Column("TEXT", required=True, description="ID пользователя")
        name = Column("TEXT", description="Имя пользователя")
        balance = Column("INTEGER", default="0", description="Баланс")
        xp = Column("INTEGER", default="0", description="Опыт")
        level = Column("INTEGER", default="1", description="Уровень")
        roles = Column("TEXT", default="'[]'", description="Роли")
        
        INDEXES = [
            Index("idx_users_id", ["user_id"], unique=True)
        ]
    
    class Moderation(TableSchema):
        """Таблица модерации"""
        user_id = Column("TEXT", required=True, description="ID пользователя")
        guild_id = Column("TEXT", required=True, description="ID сервера")
        moderator_id = Column("TEXT", required=True, description="ID модератора")
        type = Column("TEXT", required=True, description="Тип наказания")
        reason = Column("TEXT", description="Причина")
        expires_at = Column("DATETIME", description="Дата окончания")
        active = Column("BOOLEAN", default="TRUE", description="Активно")
        
        INDEXES = [
            Index("idx_mod_user", ["user_id", "guild_id", "type"]),
            Index("idx_mod_active", ["active"])
        ]
    
    class TempRooms(TableSchema):
        """Таблица временных комнат"""
        channel_id = Column("TEXT", required=True, description="ID канала")
        guild_id = Column("TEXT", required=True, description="ID сервера")
        owner_id = Column("TEXT", required=True, description="ID владельца")
        name = Column("TEXT", required=True, description="Название")
        settings = Column("TEXT", default="'{}'", description="Настройки в JSON")
        
        INDEXES = [
            Index("idx_temp_channel", ["channel_id"], unique=True),
            Index("idx_temp_owner", ["owner_id", "guild_id"])
        ]
    
    class Settings(TableSchema):
        """Таблица настроек"""
        guild_id = Column("TEXT", required=True, description="ID сервера")
        category = Column("TEXT", required=True, description="Категория")
        key = Column("TEXT", required=True, description="Ключ")
        value = Column("TEXT", required=True, description="Значение")
        
        INDEXES = [
            Index("idx_settings", ["guild_id", "category", "key"], unique=True)
        ]

# Генерируем схему после определения всех классов
Tables.SCHEMA = get_schema(Tables)