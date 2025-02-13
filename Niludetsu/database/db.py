import os, aiosqlite, asyncio
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from .tables import Tables

class Database:
    _initialized = False
    _init_lock = asyncio.Lock()
    
    def __init__(self, db_path: str = "data/database.db"):
        """Инициализация базы данных"""
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._pool = []
        self._pool_lock = asyncio.Lock()
        self._max_connections = 5  # Уменьшаем количество соединений
        
    async def _create_connection(self) -> aiosqlite.Connection:
        """Создает новое соединение с базой данных"""
        conn = await aiosqlite.connect(self.db_path)
        conn.row_factory = aiosqlite.Row
        return conn
        
    async def acquire(self) -> aiosqlite.Connection:
        """Получает соединение из пула"""
        async with self._pool_lock:
            if not self._pool:
                return await self._create_connection()
            return self._pool.pop()
            
    async def release(self, conn: aiosqlite.Connection):
        """Возвращает соединение в пул"""
        if len(self._pool) < self._max_connections:
            self._pool.append(conn)
        else:
            await conn.close()
    
    async def init(self):
        """Инициализация базы данных"""
        # Используем блокировку для предотвращения повторной инициализации
        async with Database._init_lock:
            if Database._initialized:
                return
                
            conn = await self._create_connection()
            try:
                # Получаем существующие таблицы
                cursor = await conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                existing = {row[0] for row in await cursor.fetchall()}
                
                # Создаем/обновляем таблицы
                for table_name, schema in Tables.SCHEMA.items():
                    if table_name not in existing:
                        # Создаем таблицу
                        columns = [f"{col} {type_}" for col, type_ in schema.items() if col != "INDEXES"]
                        await conn.execute(f"CREATE TABLE {table_name} ({', '.join(columns)})")
                        
                        # Создаем индексы
                        if "INDEXES" in schema:
                            for index in schema["INDEXES"]:
                                await conn.execute(index)
                                
                await conn.commit()
                Database._initialized = True
                
            finally:
                await conn.close()
    
    async def execute(self, query: str, *args) -> Optional[List[tuple]]:
        """Выполняет SQL запрос
        
        Args:
            query (str): SQL запрос
            *args: Параметры запроса
            
        Returns:
            Optional[List[tuple]]: Результат запроса, если есть
        """
        if not self._initialized:
            await self.init()
        
        conn = await self._create_connection()
        try:
            if args and isinstance(args[0], (tuple, list)):
                cursor = await conn.execute(query, args[0])
            else:
                cursor = await conn.execute(query, args)
            await conn.commit()
            result = await cursor.fetchall()
            return result
        except Exception as e:
            print(f"❌ Ошибка выполнения запроса: {e}")
            raise e
        finally:
            await conn.close()
    
    async def fetch_one(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """Получает одну запись"""
        conn = await self.acquire()
        try:
            cursor = await conn.execute(query, args)
            if row := await cursor.fetchone():
                return dict(row)
            return None
        finally:
            await self.release(conn)
    
    async def fetch_all(self, query: str, *args) -> List[Dict[str, Any]]:
        """Получает все записи"""
        conn = await self.acquire()
        try:
            cursor = await conn.execute(query, args)
            return [dict(row) for row in await cursor.fetchall()]
        finally:
            await self.release(conn)
    
    async def get_row(self, table: str, **where) -> Optional[Dict[str, Any]]:
        """Получает запись по условиям"""
        conditions = " AND ".join(f"{k} = ?" for k in where)
        query = f"SELECT * FROM {table}"
        query += f" WHERE {conditions}" if where else ""
        return await self.fetch_one(query, *where.values())
    
    async def get_rows(self, table: str, **where) -> List[Dict[str, Any]]:
        """Получает все записи по условиям"""
        conditions = " AND ".join(f"{k} = ?" for k in where)
        query = f"SELECT * FROM {table}"
        query += f" WHERE {conditions}" if where else ""
        return await self.fetch_all(query, *where.values())
    
    async def update(self, table: str, where: Dict[str, Any], values: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Обновляет запись"""
        if not values:
            return await self.get_row(table, **where)
            
        set_clause = ", ".join(f"{k} = ?" for k in values)
        where_clause = " AND ".join(f"{k} = ?" for k in where)
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        
        await self.execute(query, *values.values(), *where.values())
        return await self.get_row(table, **where)
    
    async def insert(self, table: str, values: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Вставляет запись"""
        columns = ", ".join(values.keys())
        placeholders = ", ".join("?" * len(values))
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        await self.execute(query, *values.values())
        return await self.get_row(table, **values)
    
    async def delete(self, table: str, **where) -> bool:
        """Удаляет записи по условиям"""
        conditions = " AND ".join(f"{k} = ?" for k in where)
        query = f"DELETE FROM {table} WHERE {conditions}"
        await self.execute(query, *where.values())
        return True

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
        
    async def close(self):
        """Закрывает все соединения в пуле"""
        if self._pool:
            async with self._pool_lock:
                for conn in self._pool:
                    await conn.close()
                self._pool = []