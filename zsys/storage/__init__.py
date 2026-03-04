"""Storage backends — unified entry-point for all Database and BaseStorage drivers.

Re-exports every storage backend and the ``create_database`` factory function.
Two storage families are provided: ``Database`` (modular key-value with ORM support)
and ``BaseStorage`` (flat async key-value).
"""
# RU: Модуль хранилищ — единая точка входа для всех драйверов Database и BaseStorage.
# RU: Реэкспортирует все бэкенды и фабричную функцию create_database.

from .base import (
    BaseStorage,
    Database,
    DatabaseError,
    DatabaseProtocol,
    MemoryStorage,
    MigrationError,
)
from .duckdb import DuckDBDatabase
from .factory import DbType, create_database
from .lmdb import LMDBDatabase
from .mongodb import MongoDatabase
from .orm import DatabaseSession, ORMConfig, get_db, init_db
from .pickledb import PickleDBDatabase
from .redis import RedisDatabase

# Database implementations
from .sqlite import SqliteDatabase
from .tinydb import TinyDBDatabase

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
