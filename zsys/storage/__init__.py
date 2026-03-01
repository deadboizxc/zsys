"""
Storage backends module.

Unified storage module combining Database and IStorage implementations.

Database backends (Database class - modular storage):
    - sqlite: Local file database (default)
    - duckdb: Analytical database
    - mongodb: NoSQL server database
    - redis: Key-value store
    - lmdb: Lightning Memory-Mapped Database
    - tinydb: JSON-based database
    - pickledb: Simple pickle-based database

IStorage implementations (BaseStorage subclasses - simple key-value):
    - MemoryStorage: In-memory storage (built-in)

ORM support:
    - ORMConfig: Database configuration
    - DatabaseSession: Session management with pooling
    - init_db: Initialize database tables
    - get_db: Dependency injection for sessions

Usage:
    # Database class usage (modular storage)
    from zsys.storage import create_database, Database
    db = create_database(file_path="app.sqlite3", db_type="sqlite")
    db.set("users", "count", 100)
    
    # IStorage interface usage (key-value storage)
    from zsys.storage import MemoryStorage
    storage = MemoryStorage()
    await storage.connect()
    await storage.set("session:123", {"user_id": 1})
"""

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
