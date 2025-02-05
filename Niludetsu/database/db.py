import os
import aiosqlite
from typing import Optional, Dict, Any, List, Union, Set
from datetime import datetime

from .tables import Tables

class Database:
    def __init__(self, db_path: str = "data/database.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._connection = None
        
    async def _get_existing_tables(self) -> Set[str]:
        """Получить список существующих таблиц"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = await cursor.fetchall()
            return {table[0] for table in tables}
    
    async def _get_table_columns(self, table: str) -> Dict[str, str]:
        """Получить информацию о колонках таблицы"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(f"PRAGMA table_info({table})")
            columns = await cursor.fetchall()
            return {col[1]: col[2].upper() for col in columns}
    
    async def verify_database(self):
        """Проверить и обновить структуру базы данных"""
        try:
            # Получаем существующие таблицы
            existing_tables = await self._get_existing_tables()
            
            async with aiosqlite.connect(self.db_path) as db:
                # Удаляем лишние таблицы
                for table in existing_tables:
                    if table not in Tables.SCHEMA and table != "sqlite_sequence":
                        try:
                            await db.execute(f"DROP TABLE IF EXISTS {table}")
                        except aiosqlite.OperationalError:
                            continue
                
                # Создаём или обновляем нужные таблицы
                for table_name, columns in Tables.SCHEMA.items():
                    try:
                        if table_name not in existing_tables:
                            # Создаём новую таблицу
                            columns_sql = ", ".join(f"{col} {type_}" for col, type_ in columns.items())
                            await db.execute(f"""
                                CREATE TABLE {table_name} (
                                    {columns_sql}
                                )
                            """)
                        else:
                            # Проверяем структуру существующей таблицы
                            existing_columns = await self._get_table_columns(table_name)
                            
                            # Проверяем, нужно ли обновить структуру
                            needs_update = False
                            for col, type_ in columns.items():
                                if col not in existing_columns:
                                    needs_update = True
                                    break
                                elif existing_columns[col] != type_.upper():
                                    needs_update = True
                                    break
                            
                            if needs_update:
                                # Создаём временную таблицу с новой структурой
                                temp_table = f"temp_{table_name}"
                                columns_sql = ", ".join(f"{col} {type_}" for col, type_ in columns.items())
                                await db.execute(f"""
                                    CREATE TABLE {temp_table} (
                                        {columns_sql}
                                    )
                                """)
                                
                                # Копируем данные из существующих колонок
                                common_columns = set(columns.keys()) & set(existing_columns.keys())
                                if common_columns:
                                    columns_to_copy = ", ".join(common_columns)
                                    await db.execute(f"""
                                        INSERT INTO {temp_table} ({columns_to_copy})
                                        SELECT {columns_to_copy} FROM {table_name}
                                    """)
                                
                                # Удаляем старую таблицу и переименовываем временную
                                await db.execute(f"DROP TABLE {table_name}")
                                await db.execute(f"ALTER TABLE {temp_table} RENAME TO {table_name}")
                    except aiosqlite.OperationalError as e:
                        if "already exists" in str(e):
                            # Игнорируем ошибку, если таблица уже существует
                            continue
                        else:
                            raise
                
                await db.commit()
        except Exception as e:
            print(f"❌ Ошибка при проверке базы данных: {str(e)}")
            raise

    async def init(self):
        """Инициализация базы данных"""
        await self.verify_database()
    
    async def execute(self, query: str, *args) -> Optional[List[tuple]]:
        """Выполнить SQL запрос"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(query, args[0] if len(args) == 1 and isinstance(args[0], (tuple, list)) else args)
            result = await cursor.fetchall()
            await db.commit()
            return result
    
    async def fetch_one(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """Получить одну запись"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, args) as cursor:
                if row := await cursor.fetchone():
                    return dict(row)
                return None
    
    async def fetch_all(self, query: str, *args) -> List[Dict[str, Any]]:
        """Получить все записи"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, args) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def get_row(self, table: str, **where) -> Optional[Dict[str, Any]]:
        """Получить запись по условиям"""
        where_clause = " AND ".join(f"{k} = ?" for k in where.keys())
        return await self.fetch_one(
            f"SELECT * FROM {table} WHERE {where_clause}",
            *where.values()
        )
    
    async def get_rows(self, table: str, **where) -> List[Dict[str, Any]]:
        """Получить все записи по условиям"""
        where_clause = " AND ".join(f"{k} = ?" for k in where.keys())
        query = f"SELECT * FROM {table}"
        if where:
            query += f" WHERE {where_clause}"
        return await self.fetch_all(query, *where.values())
    
    async def update(
        self,
        table: str,
        where: Dict[str, Any],
        values: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Обновить запись"""
        if not values:
            return await self.get_row(table, **where)
            
        set_clause = ", ".join(f"{k} = ?" for k in values.keys())
        where_clause = " AND ".join(f"{k} = ?" for k in where.keys())
        
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        params = list(values.values()) + list(where.values())
        
        await self.execute(query, *params)
        return await self.get_row(table, **where)
    
    async def insert(
        self,
        table: str,
        values: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Вставить запись"""
        columns = ", ".join(values.keys())
        placeholders = ", ".join("?" * len(values))
        
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        await self.execute(query, *values.values())
        
        # Получаем вставленную запись
        where_clause = " AND ".join(f"{k} = ?" for k in values.keys())
        return await self.fetch_one(
            f"SELECT * FROM {table} WHERE {where_clause}",
            *values.values()
        )

    async def ensure_user(self, user_id: Union[str, int]) -> Dict[str, Any]:
        """
        Получает данные пользователя или создает новую запись, если пользователь не существует
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Dict[str, Any]: Данные пользователя
        """
        user_data = await self.get_row("users", user_id=str(user_id))
        if not user_data:
            user_data = await self.insert("users", {
                'user_id': str(user_id),
                'balance': 0,
                'deposit': 0,
                'xp': 0,
                'level': 1,
                'roles': '[]'
            })
        return user_data

    async def connect(self) -> None:
        """Установить соединение с базой данных"""
        await self.init()
        
    async def close(self) -> None:
        """Закрыть соединение с базой данных"""
        if self._connection:
            await self._connection.close()
            self._connection = None