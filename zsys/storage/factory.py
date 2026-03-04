# core/db/factory.py — Фабрика создания БД
"""Factory for constructing Database instances — one entry point for all backends.

Provides ``create_database``, a single factory function that selects the correct
backend module at call time (lazy import) and returns a ready-to-use ``Database``
instance.  Each backend is imported only when requested, so unused drivers are
never loaded.
"""
# RU: Фабрика создания экземпляров баз данных.
# RU: Один вызов — любой бэкенд; драйверы импортируются лениво при первом обращении.

import platform
from pathlib import Path
from typing import Dict, Final, Optional, Union

from .base import Database


class DbType:
    """String constants that identify each supported database backend.

    Attributes:
        SQLITE: Identifier for the SQLite backend.
        DUCKDB: Identifier for the DuckDB backend.
        MONGODB: Identifier for the MongoDB backend.
        REDIS: Identifier for the Redis backend.
        LMDB: Identifier for the LMDB backend.
        TINYDB: Identifier for the TinyDB backend.
        PICKLEDB: Identifier for the PickleDB backend.
    """

    # RU: Строковые константы для выбора бэкенда базы данных.
    SQLITE: Final[str] = "sqlite"
    DUCKDB: Final[str] = "duckdb"
    MONGODB: Final[str] = "mongodb"
    REDIS: Final[str] = "redis"
    LMDB: Final[str] = "lmdb"
    TINYDB: Final[str] = "tinydb"
    PICKLEDB: Final[str] = "pickle"


# Расширения файлов для файловых БД
# RU: Сопоставление типа бэкенда с расширением файла для файловых БД.
DB_EXTENSIONS: Dict[str, str] = {
    DbType.SQLITE: ".sqlite3",
    DbType.DUCKDB: ".duckdb",
    DbType.LMDB: ".lmdb",
    DbType.TINYDB: ".json",
    DbType.PICKLEDB: ".pickle",
}


def _is_android() -> bool:
    """Detect whether the current runtime platform is Android.

    Returns:
        ``True`` if the platform string contains ``"android"`` (case-insensitive),
        ``False`` otherwise.
    """
    # RU: Определяет, запущен ли код на платформе Android.
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
    """Instantiate and return the appropriate ``Database`` for the requested backend.

    Imports only the backend module that matches ``db_type`` (lazy import), so
    unused drivers are never loaded.  For file-based backends the correct file
    extension is appended automatically when it is missing from ``file_path``.
    DuckDB is blocked on Android because its native library is unavailable there.

    Args:
        file_path: Path to the database file used by file-based backends
            (SQLite, DuckDB, LMDB, TinyDB, PickleDB).  A safe default filename
            is used when omitted.
        db_type: Backend selector; one of the ``DbType`` string constants.
            Defaults to ``DbType.SQLITE``.
        url: MongoDB connection string (e.g. ``"mongodb://localhost:27017"``).
            Required when ``db_type`` is ``DbType.MONGODB``.
        db_name: MongoDB database name.  Required when ``db_type`` is
            ``DbType.MONGODB``.
        redis_host: Hostname or IP address of the Redis server.
            Defaults to ``"localhost"``.
        redis_port: TCP port of the Redis server.  Defaults to ``6379``.
        redis_db: Redis logical database index.  Defaults to ``0``.

    Returns:
        A fully initialised ``Database`` instance for the requested backend.

    Raises:
        ValueError: If ``db_type`` is not recognised, if ``url`` or ``db_name``
            is missing for MongoDB, or if DuckDB is requested on Android.
        ImportError: If the driver package for the requested backend is not
            installed in the current environment.

    Example:
        # SQLite
        db = create_database("app.sqlite3", db_type="sqlite")

        # Redis
        db = create_database(db_type="redis", redis_host="localhost")

        # MongoDB
        db = create_database(db_type="mongodb", url="mongodb://localhost", db_name="mydb")
    """
    # RU: Фабрика: выбирает нужный бэкенд по db_type и возвращает готовый экземпляр Database.
    file_path_str = str(file_path) if file_path else None

    # Добавить расширение если нужно
    # RU: Автоматически дополняет путь к файлу стандартным расширением бэкенда.
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
    # RU: DuckDB не имеет нативной библиотеки для Android — явно блокируем.
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
