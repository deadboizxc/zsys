"""Storage backends — unified entry-point for all Database and BaseStorage drivers.

Re-exports every storage backend and the ``create_database`` factory function.
Two storage families are provided: ``Database`` (modular key-value with ORM support)
and ``BaseStorage`` (flat async key-value).
"""
# RU: Модуль хранилищ — единая точка входа для всех драйверов Database и BaseStorage.
# RU: Реэкспортирует все бэкенды и фабричную функцию create_database.

from .base import (
    Database,
    DatabaseProtocol,
    DatabaseError,
    MigrationError,
    BaseStorage,
    MemoryStorage,
)
from .factory import create_database, DbType
from .orm import ORMConfig, DatabaseSession, init_db, get_db

# Database implementations
from .sqlite import SqliteDatabase
from .redis import RedisDatabase
from .mongodb import MongoDatabase
from .duckdb import DuckDBDatabase
from .lmdb import LMDBDatabase
from .tinydb import TinyDBDatabase
from .pickledb import PickleDBDatabase

__all__ = [
    # Factory
    "create_database",
    "DbType",
    # Base classes
    "Database",
    "DatabaseProtocol",
    "DatabaseError",
    "MigrationError",
    # ORM
    "ORMConfig",
    "DatabaseSession",
    "init_db",
    "get_db",
    # Database implementations
    "SqliteDatabase",
    "RedisDatabase",
    "MongoDatabase",
    "DuckDBDatabase",
    "LMDBDatabase",
    "TinyDBDatabase",
    "PickleDBDatabase",
    # IStorage base and implementations
    "BaseStorage",
    "MemoryStorage",
]
