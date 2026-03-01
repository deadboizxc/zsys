# core/db/factory.py — Фабрика создания БД
"""
Фабричный метод для создания экземпляров баз данных.
"""

import platform
from pathlib import Path
from typing import Optional, Union, Final, Dict

from .base import Database


class DbType:
    """Типы поддерживаемых баз данных."""
    SQLITE: Final[str] = "sqlite"
    DUCKDB: Final[str] = "duckdb"
    MONGODB: Final[str] = "mongodb"
    REDIS: Final[str] = "redis"
    LMDB: Final[str] = "lmdb"
    TINYDB: Final[str] = "tinydb"
    PICKLEDB: Final[str] = "pickle"


# Расширения файлов для файловых БД
DB_EXTENSIONS: Dict[str, str] = {
    DbType.SQLITE: ".sqlite3",
    DbType.DUCKDB: ".duckdb",
    DbType.LMDB: ".lmdb",
    DbType.TINYDB: ".json",
    DbType.PICKLEDB: ".pickle",
}


def _is_android() -> bool:
    """Проверяет, запущен ли код на Android."""
    return "android" in platform.platform().lower()


def create_database(
    file_path: Optional[Union[str, Path]] = None,
    db_type: str = DbType.SQLITE,
    url: Optional[str] = None,
    db_name: Optional[str] = None,
    redis_host: str = "localhost",
    redis_port: int = 6379,
    redis_db: int = 0,
) -> Database:
    """
    Фабрика для создания экземпляров баз данных.

    Args:
        file_path: Путь к файлу БД (для sqlite, duckdb, lmdb, tinydb, pickledb)
        db_type: Тип БД (sqlite, mongodb, redis, duckdb, lmdb, tinydb, pickle)
        url: Строка подключения для MongoDB
        db_name: Имя БД для MongoDB
        redis_host: Хост Redis сервера
        redis_port: Порт Redis сервера
        redis_db: Номер БД Redis

    Returns:
        Экземпляр Database

    Raises:
        ValueError: При неподдерживаемом типе БД или некорректных параметрах
        ImportError: При отсутствии драйвера БД

    Example:
        # SQLite
        db = create_database("app.sqlite3", db_type="sqlite")
        
        # Redis
        db = create_database(db_type="redis", redis_host="localhost")
        
        # MongoDB
        db = create_database(db_type="mongodb", url="mongodb://localhost", db_name="mydb")
    """
    file_path_str = str(file_path) if file_path else None
    
    # Добавить расширение если нужно
    if file_path_str and db_type in DB_EXTENSIONS:
        if not file_path_str.endswith(DB_EXTENSIONS[db_type]):
            file_path_str += DB_EXTENSIONS[db_type]
    
    # SQLite
    if db_type == DbType.SQLITE:
        from .sqlite import SqliteDatabase
        if not file_path_str:
            file_path_str = "data.sqlite3"
        return SqliteDatabase(file_path_str)
    
    # DuckDB (недоступна на Android)
    if db_type == DbType.DUCKDB:
        if _is_android():
            raise ValueError("DuckDB не поддерживается на Android")
        from .duckdb import DuckDBDatabase
        if not file_path_str:
            file_path_str = "data.duckdb"
        return DuckDBDatabase(file_path_str)
    
    # MongoDB
    if db_type == DbType.MONGODB:
        from .mongodb import MongoDatabase
        if not url or not db_name:
            raise ValueError("MongoDB требует url и db_name")
        return MongoDatabase(url, db_name)
    
    # Redis
    if db_type == DbType.REDIS:
        from .redis import RedisDatabase
        return RedisDatabase(host=redis_host, port=redis_port, db=redis_db)
    
    # LMDB
    if db_type == DbType.LMDB:
        from .lmdb import LMDBDatabase
        if not file_path_str:
            file_path_str = "data.lmdb"
        return LMDBDatabase(file_path_str)
    
    # TinyDB
    if db_type == DbType.TINYDB:
        from .tinydb import TinyDBDatabase
        if not file_path_str:
            file_path_str = "data.json"
        return TinyDBDatabase(file_path_str)
    
    # PickleDB
    if db_type == DbType.PICKLEDB:
        from .pickledb import PickleDBDatabase
        if not file_path_str:
            file_path_str = "data.pickle"
        return PickleDBDatabase(file_path_str)
    
    raise ValueError(f"Неподдерживаемый тип БД: {db_type}")


__all__ = [
    "create_database",
    "DbType",
    "DB_EXTENSIONS",
]
