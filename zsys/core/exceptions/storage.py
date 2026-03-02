"""ZSYS storage and database exceptions — persistence-layer errors.

Raised by storage backends (SQLite, Redis, DuckDB, etc.) and ORM
layers when database or storage operations fail.
"""
# RU: Исключения хранилища и базы данных — ошибки уровня персистентности.
# RU: Возникают в бэкендах хранилищ и ORM при сбоях операций с данными.

from .base import BaseException


class DatabaseError(BaseException):
    """Exception raised when a database operation fails.

    Raised for connection failures, query errors, constraint violations,
    migration failures, and other SQL/ORM-level problems.

    Attributes:
        message: Human-readable error description.
        code: Optional error code string.
    """
    # RU: Исключение при сбое операции с базой данных.
    pass


class StorageError(BaseException):
    """Exception raised when a key-value storage operation fails.

    Raised by IStorage backends (Redis, SQLite KV, LMDB, etc.) when
    read/write/delete operations cannot be completed.

    Attributes:
        message: Human-readable error description.
        code: Optional error code string.
    """
    # RU: Исключение при сбое операции с хранилищем ключ-значение.
    pass


__all__ = [
    "DatabaseError",
    "StorageError",
]
