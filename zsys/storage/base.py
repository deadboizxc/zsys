# core/storage/base.py — Base classes for storage implementations
"""
Base classes and interfaces for all storage drivers.

Two types of storage:
1. Database - modular storage with module:variable structure (for config management)
2. IStorage implementations - simple key-value storage (for cache, sessions, etc.)
"""

import logging
import fnmatch
import time
from typing import Any, Dict, Optional, TypeVar, Protocol, runtime_checkable, Tuple
from abc import ABC, abstractmethod
from collections.abc import MutableMapping
from contextlib import AbstractContextManager

T = TypeVar('T')

# Simple logger without external dependencies
_logger = logging.getLogger("zsys.storage")


@runtime_checkable
class DatabaseProtocol(Protocol):
    """
    Протокол для проверки совместимости классов баз данных.
    """
    
    def get(self, module: str, variable: str, default: Optional[T] = None) -> Optional[T]:
        """Получает значение из БД по ключу."""
        ...

    def set(self, module: str, variable: str, value: Any) -> None:
        """Устанавливает значение в БД."""
        ...

    def remove(self, module: str, variable: str) -> None:
        """Удаляет значение по ключу."""
        ...

    def get_collection(self, module: str) -> Dict[str, Any]:
        """Получает все данные модуля."""
        ...

    def close(self) -> None:
        """Закрывает соединение с БД."""
        ...


class Database(AbstractContextManager, MutableMapping, ABC):
    """
    Абстрактный класс для работы с базой данных.
    
    Реализует интерфейсы:
        - MutableMapping: для использования как словарь (db["key"] = value)
        - AbstractContextManager: для использования в контексте with
    
    Все драйверы БД наследуются от этого класса.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Инициализация базы данных.
        
        Args:
            logger: Логгер для вывода информации. По умолчанию core.db.
        """
        self._logger = logger or _logger
    
    @property
    def logger(self) -> logging.Logger:
        """Возвращает логгер БД."""
        return self._logger
    
    @abstractmethod
    def get(self, module: str, variable: str, default: Optional[T] = None) -> Optional[T]:
        """
        Получает значение по ключу из базы данных.
        
        Args:
            module: Название модуля/таблицы/коллекции
            variable: Ключ переменной
            default: Значение по умолчанию
        
        Returns:
            Значение или default если не найдено
        """
        pass
    
    @abstractmethod
    def set(self, module: str, variable: str, value: Any) -> None:
        """
        Записывает значение в базу данных.
        
        Args:
            module: Название модуля/таблицы/коллекции
            variable: Ключ переменной
            value: Значение для записи
        """
        pass
    
    @abstractmethod
    def remove(self, module: str, variable: str) -> None:
        """
        Удаляет значение по ключу.
        
        Args:
            module: Название модуля/таблицы/коллекции
            variable: Ключ для удаления
        """
        pass
    
    @abstractmethod
    def get_collection(self, module: str) -> Dict[str, Any]:
        """
        Получает все данные модуля.
        
        Args:
            module: Название модуля/таблицы/коллекции
        
        Returns:
            Словарь {variable: value}
        """
        pass
    
    @abstractmethod
    def get_modules(self) -> list:
        """
        Получает список всех модулей/таблиц в БД.
        
        Returns:
            Список названий модулей
        """
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Закрывает соединение с базой данных."""
        pass
    
    # === MutableMapping interface ===
    
    def __getitem__(self, key: str) -> Any:
        """Получает значение по ключу формата 'module.variable'."""
        module, variable = self._split_key(key)
        value = self.get(module, variable)
        if value is None:
            raise KeyError(key)
        return value
    
    def __setitem__(self, key: str, value: Any) -> None:
        """Устанавливает значение по ключу формата 'module.variable'."""
        module, variable = self._split_key(key)
        self.set(module, variable, value)
    
    def __delitem__(self, key: str) -> None:
        """Удаляет ключ формата 'module.variable'."""
        module, variable = self._split_key(key)
        self.remove(module, variable)
    
    def __len__(self) -> int:
        """Не поддерживается — возвращает 0."""
        return 0
    
    def __iter__(self):
        """Не поддерживается — возвращает пустой итератор."""
        return iter([])
    
    # === Context Manager ===
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Закрывает соединение при выходе из контекста."""
        self.close()
        if exc_type is not None:
            self._logger.error(f"Ошибка в контексте БД: {exc_val}")
    
    # === Helpers ===
    
    @staticmethod
    def _split_key(key: str) -> Tuple[str, str]:
        """
        Разделяет ключ на модуль и переменную.
        
        Args:
            key: Ключ в формате 'module.variable'
        
        Returns:
            Tuple (module, variable)
        
        Raises:
            ValueError: Если ключ не содержит точку
        """
        if '.' not in key:
            raise ValueError("Ключ должен быть в формате 'module.variable'")
        parts = key.split('.', 1)
        return (parts[0], parts[1])
    
    def transaction(self):
        """
        Создает контекст транзакции.
        
        Returns:
            TransactionContext
        """
        return TransactionContext(self, self._logger)
    
    def migrate(self, old_db: 'Database') -> None:
        """
        Мигрирует данные из другой БД.
        
        Args:
            old_db: Источник данных
        
        Raises:
            MigrationError: При ошибке миграции
        """
        self._logger.info("Начата миграция данных...")
        try:
            for module in old_db.get_modules():
                data = old_db.get_collection(module)
                for key, value in data.items():
                    self.set(module, key, value)
            self._logger.info("Миграция успешно завершена")
        except Exception as e:
            self._logger.error(f"Ошибка миграции: {e}")
            raise MigrationError(f"Ошибка миграции данных: {e}") from e


class TransactionContext:
    """Контекстный менеджер для транзакций."""
    
    def __init__(self, db: Database, logger: logging.Logger):
        self.db = db
        self._logger = logger
    
    def __enter__(self):
        self._logger.debug("Транзакция начата")
        return self.db
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self._logger.debug("Транзакция завершена")
        else:
            self._logger.error(f"Ошибка в транзакции: {exc_val}")


class DatabaseError(Exception):
    """Исключение для ошибок работы с БД."""
    pass


class MigrationError(DatabaseError):
    """Исключение для ошибок миграции."""
    pass


# ============================================================================
# BASE STORAGE CLASS (for IStorage implementations)
# ============================================================================

class BaseStorage(ABC):
    """
    Base class for IStorage implementations.
    
    Provides common functionality for key-value storage backends.
    All IStorage implementations should inherit from this class.
    
    Subclasses must implement:
    - connect(), disconnect()
    - get(), set(), delete()
    - exists(), clear(), keys()
    
    Optional (have default implementations):
    - mget(), mset(), mdelete()
    - expire(), ttl(), persist()
    - increment(), decrement()
    - size(), info()
    """
    
    def __init__(self):
        """Initialize base storage."""
        self._connected = False
        self._logger = logging.getLogger(f"zsys.storage.{self.__class__.__name__}")
    
    @property
    def logger(self) -> logging.Logger:
        """Get storage logger."""
        return self._logger
    
    @property
    def is_connected(self) -> bool:
        """Check if storage is connected."""
        return self._connected
    
    # ===== Abstract Methods (must be implemented) =====
    
    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to storage."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to storage."""
        pass
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value by key."""
        pass
    
    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        expire: int | None = None
    ) -> None:
        """Set key-value pair with optional expiration."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete key from storage. Returns True if deleted."""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in storage."""
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all data from storage."""
        pass
    
    @abstractmethod
    async def keys(self, pattern: str = "*") -> list[str]:
        """Get all keys matching pattern."""
        pass
    
    # ===== Default Implementations (can be overridden) =====
    
    async def mget(self, keys: list[str]) -> list[Optional[Any]]:
        """Get multiple values by keys (default implementation)."""
        return [await self.get(key) for key in keys]
    
    async def mset(self, mapping: dict[str, Any]) -> None:
        """Set multiple key-value pairs (default implementation)."""
        for key, value in mapping.items():
            await self.set(key, value)
    
    async def mdelete(self, keys: list[str]) -> int:
        """Delete multiple keys (default implementation)."""
        count = 0
        for key in keys:
            if await self.delete(key):
                count += 1
        return count
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration time for a key (default: not supported)."""
        return False
    
    async def ttl(self, key: str) -> int:
        """Get remaining TTL for a key (default: -1 = no expiration)."""
        return -1 if await self.exists(key) else -2
    
    async def persist(self, key: str) -> bool:
        """Remove expiration from a key (default: not supported)."""
        return False
    
    async def increment(self, key: str, delta: int = 1) -> int:
        """Increment numeric value by delta (default implementation)."""
        value = await self.get(key)
        new_value = (int(value) if value is not None else 0) + delta
        await self.set(key, new_value)
        return new_value
    
    async def decrement(self, key: str, delta: int = 1) -> int:
        """Decrement numeric value by delta (default implementation)."""
        return await self.increment(key, -delta)
    
    async def size(self) -> int:
        """Get number of keys in storage (default implementation)."""
        return len(await self.keys())
    
    async def info(self) -> dict[str, Any]:
        """Get storage information (default implementation)."""
        return {
            "backend": self.__class__.__name__,
            "connected": self._connected,
            "keys": await self.size(),
        }
    
    # ===== Helper Methods =====
    
    def _match_pattern(self, key: str, pattern: str) -> bool:
        """Helper method to match key against pattern."""
        return fnmatch.fnmatch(key, pattern)


class MemoryStorage(BaseStorage):
    """
    In-memory implementation of IStorage interface.
    
    Dictionary-based storage in RAM with full TTL support.
    Fast but data is lost when program exits.
    
    Features:
    - Batch operations (mget, mset, mdelete)
    - TTL/expiration support with automatic cleanup
    - Atomic increment/decrement operations
    - Pattern-based key search
    
    Ideal for:
    - Testing
    - Temporary data
    - Caching (without persistence)
    - Development environments
    
    Usage:
        storage = MemoryStorage()
        await storage.connect()
        
        # Basic operations
        await storage.set("key", "value")
        value = await storage.get("key")
        
        # With expiration
        await storage.set("session:123", {"user_id": 123}, expire=3600)
        
        # Batch operations
        await storage.mset({"key1": "val1", "key2": "val2"})
        values = await storage.mget(["key1", "key2"])
        
        # Atomic operations
        await storage.increment("counter", 5)
        await storage.decrement("counter", 1)
        
        await storage.disconnect()
    """
    
    def __init__(self):
        """Initialize memory storage."""
        super().__init__()
        self._data: Dict[str, Any] = {}
        self._expiry: Dict[str, float] = {}  # key -> expiration timestamp
    
    def _cleanup_expired(self) -> None:
        """Remove expired keys from storage."""
        now = time.time()
        expired_keys = [
            key for key, expiry_time in self._expiry.items()
            if expiry_time <= now
        ]
        for key in expired_keys:
            self._data.pop(key, None)
            self._expiry.pop(key, None)
    
    def _is_expired(self, key: str) -> bool:
        """Check if key is expired."""
        if key not in self._expiry:
            return False
        return time.time() >= self._expiry[key]
    
    async def connect(self) -> None:
        """Establish connection (just sets flag)."""
        self.logger.info("Connecting to memory storage")
        self._connected = True
        self.logger.info("Connected to memory storage")
    
    async def disconnect(self) -> None:
        """Close connection and clear data."""
        self.logger.info("Disconnecting from memory storage")
        self._data.clear()
        self._expiry.clear()
        self._connected = False
        self.logger.info("Disconnected from memory storage")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value by key. Returns None if key doesn't exist or is expired."""
        if self._is_expired(key):
            await self.delete(key)
            return None
        return self._data.get(key)
    
    async def set(
        self,
        key: str,
        value: Any,
        expire: int | None = None
    ) -> None:
        """Set key-value pair with optional expiration in seconds."""
        self._data[key] = value
        
        if expire is not None:
            self._expiry[key] = time.time() + expire
        elif key in self._expiry:
            # Remove expiration if setting without expire parameter
            del self._expiry[key]
    
    async def delete(self, key: str) -> bool:
        """Delete key from storage. Returns True if key was deleted."""
        existed = key in self._data
        self._data.pop(key, None)
        self._expiry.pop(key, None)
        return existed
    
    async def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        if self._is_expired(key):
            await self.delete(key)
            return False
        return key in self._data
    
    async def clear(self) -> None:
        """Clear all data from storage."""
        self._data.clear()
        self._expiry.clear()
        self.logger.info("Cleared all data from memory storage")
    
    async def keys(self, pattern: str = "*") -> list[str]:
        """Get all keys matching pattern (excludes expired keys)."""
        self._cleanup_expired()
        all_keys = list(self._data.keys())
        
        if pattern != "*":
            all_keys = [k for k in all_keys if self._match_pattern(k, pattern)]
        
        return all_keys
    
    # ===== Optimized Batch Operations =====
    
    async def mget(self, keys: list[str]) -> list[Optional[Any]]:
        """Get multiple values by keys. Optimized for memory storage."""
        return [await self.get(key) for key in keys]
    
    async def mset(self, mapping: dict[str, Any]) -> None:
        """Set multiple key-value pairs. Optimized for memory storage."""
        for key, value in mapping.items():
            await self.set(key, value)
    
    async def mdelete(self, keys: list[str]) -> int:
        """Delete multiple keys. Returns count of deleted keys."""
        count = 0
        for key in keys:
            if await self.delete(key):
                count += 1
        return count
    
    # ===== TTL Operations =====
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration time for a key. Returns True if key exists."""
        if not await self.exists(key):
            return False
        self._expiry[key] = time.time() + seconds
        return True
    
    async def ttl(self, key: str) -> int:
        """
        Get remaining TTL for a key in seconds.
        
        Returns:
            -2: key does not exist
            -1: key exists but has no expiration
            >0: remaining time in seconds
        """
        if not await self.exists(key):
            return -2
        
        if key not in self._expiry:
            return -1
        
        remaining = int(self._expiry[key] - time.time())
        return max(0, remaining)
    
    async def persist(self, key: str) -> bool:
        """Remove expiration from a key. Returns True if expiration was removed."""
        if key not in self._expiry:
            return False
        del self._expiry[key]
        return True
    
    # ===== Atomic Operations =====
    
    async def increment(self, key: str, delta: int = 1) -> int:
        """
        Increment numeric value by delta atomically.
        
        If key doesn't exist, it's set to 0 before incrementing.
        Returns the new value.
        """
        value = await self.get(key)
        new_value = (int(value) if value is not None else 0) + delta
        await self.set(key, new_value)
        return new_value
    
    async def decrement(self, key: str, delta: int = 1) -> int:
        """
        Decrement numeric value by delta atomically.
        
        If key doesn't exist, it's set to 0 before decrementing.
        Returns the new value.
        """
        return await self.increment(key, -delta)
    
    # ===== Metadata Operations =====
    
    async def size(self) -> int:
        """Get number of keys in storage (excludes expired keys)."""
        self._cleanup_expired()
        return len(self._data)
    
    async def info(self) -> dict[str, Any]:
        """Get detailed storage information."""
        self._cleanup_expired()
        keys_with_ttl = len(self._expiry)
        return {
            "backend": "MemoryStorage",
            "connected": self._connected,
            "keys": len(self._data),
            "keys_with_ttl": keys_with_ttl,
            "keys_without_ttl": len(self._data) - keys_with_ttl,
            "memory_usage": "in-memory",
        }


__all__ = [
    # Database (modular storage)
    "Database",
    "DatabaseProtocol",
    "DatabaseError",
    "MigrationError",
    "TransactionContext",
    # IStorage implementations
    "BaseStorage",
    "MemoryStorage",
]
