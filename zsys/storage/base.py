# core/storage/base.py — Base classes for storage implementations
"""Storage base classes and interfaces — abstract foundation for all backends.

Defines two storage families: ``Database`` (modular key-value organised by
module/variable) and ``BaseStorage`` (flat async key-value with TTL).
All concrete drivers inherit from one of these two abstract classes.
"""
# RU: Базовые классы и интерфейсы для всех хранилищ.
# RU: Два семейства: Database (модульное хранилище) и BaseStorage (ключ-значение с TTL).

import logging
import fnmatch
import time
from typing import Any, Dict, Optional, TypeVar, Protocol, runtime_checkable, Tuple
from abc import ABC, abstractmethod
from collections.abc import MutableMapping
from contextlib import AbstractContextManager

T = TypeVar("T")

# Simple logger without external dependencies
_logger = logging.getLogger("zsys.storage")


@runtime_checkable
class DatabaseProtocol(Protocol):
    """Duck-typing compatibility Protocol for Database backends.

    Decorated with ``@runtime_checkable`` so ``isinstance(obj, DatabaseProtocol)``
    works at runtime without requiring explicit inheritance.

    Note:
        Any class that exposes ``get``, ``set``, ``remove``, ``get_collection``,
        and ``close`` with matching signatures satisfies this Protocol.
    """

    # RU: Протокол совместимости для бэкендов Database — проверяется через isinstance().

    def get(
        self, module: str, variable: str, default: Optional[T] = None
    ) -> Optional[T]:
        """Return value from the database or *default* if the key is absent."""
        # RU: Возвращает значение из БД или default если ключ не найден.
        ...

    def set(self, module: str, variable: str, value: Any) -> None:
        """Write *value* to the database under the given module and variable key."""
        # RU: Записывает значение в БД по ключу модуль+переменная.
        ...

    def remove(self, module: str, variable: str) -> None:
        """Delete the entry identified by *module* and *variable*."""
        # RU: Удаляет запись по ключу.
        ...

    def get_collection(self, module: str) -> Dict[str, Any]:
        """Return all variables belonging to *module* as a dict."""
        # RU: Возвращает все переменные модуля в виде словаря.
        ...

    def close(self) -> None:
        """Close the connection to the storage backend."""
        # RU: Закрывает соединение с хранилищем.
        ...


class Database(AbstractContextManager, MutableMapping, ABC):
    """Abstract base class for all modular key-value database backends.

    Combines ``MutableMapping`` (dict-like ``db["module.variable"]`` access)
    with ``AbstractContextManager`` (``with db:`` usage).  Keys must follow
    the ``"module.variable"`` dotted format.  Concrete drivers must implement
    :meth:`get`, :meth:`set`, :meth:`remove`, :meth:`get_collection`,
    :meth:`get_modules`, and :meth:`close`.

    Attributes:
        _logger: Logger instance used by the database and its methods.
    """

    # RU: Абстрактный базовый класс для всех модульных бэкендов хранилища ключ-значение.
    # RU: Ключи имеют формат «модуль.переменная»; поддерживает dict-интерфейс и контекстный менеджер.

    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialise the database with an optional logger.

        Args:
            logger: Logger to use for debug/error output.  Defaults to the
                ``zsys.storage`` logger when *None*.
        """
        # RU: Инициализация БД с опциональным логгером.
        self._logger = logger or _logger

    @property
    def logger(self) -> logging.Logger:
        """Return the database logger."""
        # RU: Возвращает логгер БД.
        return self._logger

    @abstractmethod
    def get(
        self, module: str, variable: str, default: Optional[T] = None
    ) -> Optional[T]:
        """Retrieve a value from the database.

        Args:
            module: Module (table/collection) name.
            variable: Variable key within the module.
            default: Value returned when the key is absent.

        Returns:
            The stored value, or *default* if not found.
        """
        # RU: Получает значение по ключу.
        pass

    @abstractmethod
    def set(self, module: str, variable: str, value: Any) -> None:
        """Persist a value in the database.

        Args:
            module: Module (table/collection) name.
            variable: Variable key within the module.
            value: Value to store.
        """
        # RU: Сохраняет значение в хранилище.
        pass

    @abstractmethod
    def remove(self, module: str, variable: str) -> None:
        """Delete a key from the database.

        Args:
            module: Module (table/collection) name.
            variable: Variable key to delete.
        """
        # RU: Удаляет ключ из хранилища.
        pass

    @abstractmethod
    def get_collection(self, module: str) -> Dict[str, Any]:
        """Return all variables stored under *module*.

        Args:
            module: Module (table/collection) name.

        Returns:
            A ``{variable: value}`` dictionary for the given module.
        """
        # RU: Возвращает все переменные модуля.
        pass

    @abstractmethod
    def get_modules(self) -> list:
        """Return a list of all module names present in the database.

        Returns:
            A list of module name strings.
        """
        # RU: Возвращает список всех модулей.
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the connection to the database backend."""
        # RU: Закрывает соединение.
        pass

    # === MutableMapping interface ===

    def __getitem__(self, key: str) -> Any:
        """Return the value at key ``'module.variable'``, raising ``KeyError`` if absent."""
        # RU: Возвращает значение по ключу «модуль.переменная»; бросает KeyError если нет.
        module, variable = self._split_key(key)
        value = self.get(module, variable)
        if value is None:
            raise KeyError(key)
        return value

    def __setitem__(self, key: str, value: Any) -> None:
        """Store *value* at key ``'module.variable'``."""
        # RU: Сохраняет значение по ключу «модуль.переменная».
        module, variable = self._split_key(key)
        self.set(module, variable, value)

    def __delitem__(self, key: str) -> None:
        """Delete the entry at key ``'module.variable'``."""
        # RU: Удаляет запись по ключу «модуль.переменная».
        module, variable = self._split_key(key)
        self.remove(module, variable)

    def __len__(self) -> int:
        """Return 0; full enumeration is not supported by this interface."""
        # RU: Возвращает 0 — полная итерация не поддерживается.
        return 0

    def __iter__(self):
        """Yield nothing; iteration is not supported by this interface."""
        # RU: Не поддерживает итерацию — возвращает пустой итератор.
        return iter([])

    # === Context Manager ===

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Close the connection on context-manager exit and log any exception."""
        # RU: Закрывает соединение при выходе из контекста; логирует исключение если есть.
        self.close()
        if exc_type is not None:
            self._logger.error(f"Ошибка в контексте БД: {exc_val}")

    # === Helpers ===

    @staticmethod
    def _split_key(key: str) -> Tuple[str, str]:
        """Split a dotted key into (module, variable) parts.

        Args:
            key: Key string in ``'module.variable'`` format.

        Returns:
            A ``(module, variable)`` tuple.

        Raises:
            ValueError: If *key* contains no dot separator.
        """
        # RU: Разделяет ключ «модуль.переменная» на кортеж (module, variable).
        if "." not in key:
            raise ValueError("Ключ должен быть в формате 'module.variable'")
        parts = key.split(".", 1)
        return (parts[0], parts[1])

    def transaction(self):
        """Create and return a TransactionContext wrapping this database.

        Returns:
            A :class:`TransactionContext` that yields ``self`` on entry.
        """
        # RU: Создаёт контекст транзакции для данной БД.
        return TransactionContext(self, self._logger)

    def migrate(self, old_db: "Database") -> None:
        """Copy all data from *old_db* into this database.

        Iterates over every module in *old_db* and calls :meth:`set` for each
        key-value pair, overwriting existing entries.

        Args:
            old_db: Source database to read data from.

        Raises:
            MigrationError: If any error occurs during the migration process.
        """
        # RU: Копирует все данные из old_db в текущую БД; при ошибке бросает MigrationError.
        self._logger.info("Начата миграция данных...")
        try:
            for module in old_db.get_modules():  # RU: Перебираем все модули источника.
                data = old_db.get_collection(module)
                for key, value in data.items():
                    self.set(module, key, value)
            self._logger.info("Миграция успешно завершена")
        except Exception as e:
            self._logger.error(f"Ошибка миграции: {e}")
            raise MigrationError(
                f"Ошибка миграции данных: {e}"
            ) from e  # RU: Оборачиваем исходное исключение.


class TransactionContext:
    """Lightweight context manager that wraps a Database transaction.

    Attributes:
        db: The wrapped :class:`Database` instance returned on ``__enter__``.
    """

    # RU: Лёгкий контекстный менеджер транзакции для Database.

    def __init__(self, db: Database, logger: logging.Logger):
        """Initialise with a database instance and its logger."""
        # RU: Сохраняет ссылку на БД и логгер.
        self.db = db
        self._logger = logger

    def __enter__(self):
        """Start the transaction and return the database."""
        # RU: Открывает транзакцию и возвращает объект БД.
        self._logger.debug("Транзакция начата")
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Commit or log-error on context exit."""
        # RU: Завершает транзакцию; логирует ошибку если было исключение.
        if exc_type is None:
            self._logger.debug("Транзакция завершена")
        else:
            self._logger.error(f"Ошибка в транзакции: {exc_val}")


class DatabaseError(Exception):
    """Base exception for all database operation errors."""

    # RU: Базовое исключение для ошибок операций с базой данных.
    pass


class MigrationError(DatabaseError):
    """Raised when a database migration fails."""

    # RU: Исключение при ошибке миграции данных.
    pass


# ============================================================================
# BASE STORAGE CLASS (for IStorage implementations)
# ============================================================================


class BaseStorage(ABC):
    """Async ABC for flat key-value storage with TTL support.

    All concrete async storage implementations must inherit from this class
    and implement the abstract methods.  Default (non-abstract) methods
    provide loop-based fallbacks that subclasses may override for efficiency.

    Abstract methods (must be implemented):
        connect, disconnect, get, set, delete, exists, clear, keys.

    Default methods (may be overridden):
        mget, mset, mdelete, expire, ttl, persist, increment, decrement,
        size, info.

    Attributes:
        _connected: Internal flag tracking connection state.
        _logger: Per-class logger under ``zsys.storage.<ClassName>``.
    """

    # RU: Абстрактный базовый класс для асинхронного плоского хранилища ключ-значение с TTL.
    # RU: Абстрактные методы: connect/disconnect/get/set/delete/exists/clear/keys.
    # RU: Методы по умолчанию: mget/mset/mdelete/expire/ttl/persist/increment/decrement/size/info.

    def __init__(self):
        """Initialise base storage state."""
        # RU: Инициализирует флаг подключения и логгер.
        self._connected = False
        self._logger = logging.getLogger(f"zsys.storage.{self.__class__.__name__}")

    @property
    def logger(self) -> logging.Logger:
        """Return the storage logger."""
        # RU: Возвращает логгер хранилища.
        return self._logger

    @property
    def is_connected(self) -> bool:
        """Return ``True`` if the backend is currently connected."""
        # RU: Возвращает True если хранилище подключено.
        return self._connected

    # ===== Abstract Methods (must be implemented) =====

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the storage backend."""
        # RU: Устанавливает соединение с хранилищем.
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close the connection to the storage backend."""
        # RU: Закрывает соединение с хранилищем.
        pass

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Return the value stored at *key*, or ``None`` if absent."""
        # RU: Возвращает значение по ключу или None.
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, expire: int | None = None) -> None:
        """Store *value* under *key* with an optional TTL in seconds."""
        # RU: Сохраняет значение по ключу с опциональным временем жизни.
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete *key* from storage and return ``True`` if it existed."""
        # RU: Удаляет ключ; возвращает True если ключ существовал.
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Return ``True`` if *key* exists and has not expired."""
        # RU: Проверяет существование ключа (с учётом TTL).
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Remove all keys from the storage."""
        # RU: Очищает всё хранилище.
        pass

    @abstractmethod
    async def keys(self, pattern: str = "*") -> list[str]:
        """Return all keys matching *pattern* (glob-style)."""
        # RU: Возвращает ключи, соответствующие паттерну.
        pass

    # ===== Default Implementations (can be overridden) =====

    async def mget(self, keys: list[str]) -> list[Optional[Any]]:
        """Return values for each key in *keys* (default loop implementation)."""
        # RU: Пакетное чтение — по умолчанию поочерёдные вызовы get().
        return [await self.get(key) for key in keys]

    async def mset(self, mapping: dict[str, Any]) -> None:
        """Store all key-value pairs in *mapping* (default loop implementation)."""
        # RU: Пакетная запись — по умолчанию поочерёдные вызовы set().
        for key, value in mapping.items():
            await self.set(key, value)

    async def mdelete(self, keys: list[str]) -> int:
        """Delete all *keys* and return the count of actually deleted entries."""
        # RU: Пакетное удаление; возвращает число удалённых ключей.
        count = 0
        for key in keys:
            if await self.delete(key):
                count += 1
        return count

    async def expire(self, key: str, seconds: int) -> bool:
        """Set a TTL of *seconds* on *key* (default: not supported, returns ``False``)."""
        # RU: Устанавливает TTL на ключ; по умолчанию не поддерживается.
        return False

    async def ttl(self, key: str) -> int:
        """Return remaining TTL seconds for *key* (``-1`` = no expiry, ``-2`` = absent)."""
        # RU: Возвращает оставшийся TTL: -1 без срока, -2 если ключ отсутствует.
        return -1 if await self.exists(key) else -2

    async def persist(self, key: str) -> bool:
        """Remove any expiration from *key* (default: not supported, returns ``False``)."""
        # RU: Снимает TTL с ключа; по умолчанию не поддерживается.
        return False

    async def increment(self, key: str, delta: int = 1) -> int:
        """Increment the numeric value at *key* by *delta* and return the new value."""
        # RU: Увеличивает числовое значение ключа на delta; создаёт с нуля если ключа нет.
        value = await self.get(key)
        new_value = (int(value) if value is not None else 0) + delta
        await self.set(key, new_value)
        return new_value

    async def decrement(self, key: str, delta: int = 1) -> int:
        """Decrement the numeric value at *key* by *delta* and return the new value."""
        # RU: Уменьшает числовое значение ключа на delta.
        return await self.increment(key, -delta)

    async def size(self) -> int:
        """Return the total number of keys currently in storage."""
        # RU: Возвращает количество ключей в хранилище.
        return len(await self.keys())

    async def info(self) -> dict[str, Any]:
        """Return a dict with basic backend metadata."""
        # RU: Возвращает метаданные о хранилище.
        return {
            "backend": self.__class__.__name__,
            "connected": self._connected,
            "keys": await self.size(),
        }

    # ===== Helper Methods =====

    def _match_pattern(self, key: str, pattern: str) -> bool:
        """Return ``True`` if *key* matches the glob *pattern*."""
        # RU: Проверяет соответствие ключа glob-паттерну.
        return fnmatch.fnmatch(key, pattern)


class MemoryStorage(BaseStorage):
    """In-memory dict-based storage with TTL support.

    Stores values in a plain Python ``dict``; expiry times are tracked as
    float UNIX timestamps in a parallel ``_expiry`` dict.  Expired entries
    are evicted lazily — on the next ``get``, ``exists``, or ``keys`` call —
    via :meth:`_cleanup_expired`.  Increment/decrement are atomic within a
    single async call because the event-loop is not yielded mid-operation.

    Attributes:
        _data: Mapping of key → stored value.
        _expiry: Mapping of key → UNIX expiry timestamp (float).
    """

    # RU: Хранилище в оперативной памяти на базе dict с поддержкой TTL.
    # RU: Просроченные записи вытесняются лениво при следующем обращении.
    # RU: Инкремент/декремент атомарны в рамках одного async-вызова.

    def __init__(self):
        """Initialise memory storage with empty data and expiry dicts."""
        # RU: Создаёт пустые словари данных и времён истечения.
        super().__init__()
        self._data: Dict[str, Any] = {}
        self._expiry: Dict[str, float] = {}  # key -> expiration timestamp

    def _cleanup_expired(self) -> None:
        """Evict all keys whose expiry timestamp is in the past."""
        # RU: Удаляет все ключи с истёкшим сроком действия.
        now = time.time()
        expired_keys = [
            key
            for key, expiry_time in self._expiry.items()
            if expiry_time
            <= now  # RU: Ключ истёк если текущее время >= времени истечения.
        ]
        for key in expired_keys:
            self._data.pop(key, None)
            self._expiry.pop(key, None)

    def _is_expired(self, key: str) -> bool:
        """Return ``True`` if *key* has a recorded expiry that has passed."""
        # RU: Возвращает True если срок действия ключа истёк.
        if key not in self._expiry:
            return False
        return time.time() >= self._expiry[key]

    async def connect(self) -> None:
        """Mark the storage as connected (no actual I/O needed)."""
        # RU: Помечает хранилище как подключённое — реального соединения нет.
        self.logger.info("Connecting to memory storage")
        self._connected = True
        self.logger.info("Connected to memory storage")

    async def disconnect(self) -> None:
        """Clear all stored data and mark the storage as disconnected."""
        # RU: Очищает данные и помечает хранилище как отключённое.
        self.logger.info("Disconnecting from memory storage")
        self._data.clear()
        self._expiry.clear()
        self._connected = False
        self.logger.info("Disconnected from memory storage")

    async def get(self, key: str) -> Optional[Any]:
        """Return the value for *key*, or ``None`` if absent or expired."""
        # RU: Возвращает значение ключа; None если ключ истёк или отсутствует.
        if self._is_expired(key):
            await self.delete(key)  # RU: Лениво вытесняем истёкший ключ.
            return None
        return self._data.get(key)

    async def set(self, key: str, value: Any, expire: int | None = None) -> None:
        """Store *value* under *key* with an optional TTL in seconds."""
        # RU: Сохраняет значение; устанавливает или снимает TTL по необходимости.
        self._data[key] = value

        if expire is not None:
            self._expiry[key] = (
                time.time() + expire
            )  # RU: Вычисляем абсолютный timestamp истечения.
        elif key in self._expiry:
            # Remove expiration if setting without expire parameter
            del self._expiry[key]

    async def delete(self, key: str) -> bool:
        """Remove *key* and its expiry record; return ``True`` if it existed."""
        # RU: Удаляет ключ и его TTL; возвращает True если ключ существовал.
        existed = key in self._data
        self._data.pop(key, None)
        self._expiry.pop(key, None)
        return existed

    async def exists(self, key: str) -> bool:
        """Return ``True`` if *key* is present and has not expired."""
        # RU: Проверяет наличие ключа с учётом TTL; лениво вытесняет истёкший.
        if self._is_expired(key):
            await self.delete(key)
            return False
        return key in self._data

    async def clear(self) -> None:
        """Remove all keys and expiry records from storage."""
        # RU: Очищает оба словаря — данные и TTL.
        self._data.clear()
        self._expiry.clear()
        self.logger.info("Cleared all data from memory storage")

    async def keys(self, pattern: str = "*") -> list[str]:
        """Return all non-expired keys matching *pattern* (glob-style)."""
        # RU: Возвращает актуальные ключи, соответствующие паттерну; сначала чистит истёкшие.
        self._cleanup_expired()
        all_keys = list(self._data.keys())

        if pattern != "*":
            all_keys = [k for k in all_keys if self._match_pattern(k, pattern)]

        return all_keys

    # ===== Optimized Batch Operations =====

    async def mget(self, keys: list[str]) -> list[Optional[Any]]:
        """Return values for each key in *keys*, respecting TTL."""
        # RU: Пакетное чтение с учётом TTL каждого ключа.
        return [await self.get(key) for key in keys]

    async def mset(self, mapping: dict[str, Any]) -> None:
        """Store all key-value pairs from *mapping* without TTL."""
        # RU: Пакетная запись без TTL.
        for key, value in mapping.items():
            await self.set(key, value)

    async def mdelete(self, keys: list[str]) -> int:
        """Delete each key in *keys* and return the count of deletions."""
        # RU: Пакетное удаление; возвращает число реально удалённых ключей.
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
        """Return remaining TTL for *key* in seconds.

        Returns:
            ``-2`` if the key does not exist; ``-1`` if the key exists but has
            no expiry; a non-negative integer representing seconds remaining.
        """
        # RU: -2 если ключа нет; -1 если нет срока действия; >0 — оставшиеся секунды.
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
        """Atomically increment a numeric value by *delta*.

        If *key* does not exist it is treated as ``0`` before incrementing.

        Args:
            key: Key whose value to increment.
            delta: Amount to add (default ``1``).

        Returns:
            The new integer value after incrementing.
        """
        # RU: Атомарно увеличивает числовое значение ключа на delta; инициализирует 0 если нет.
        value = await self.get(key)
        new_value = (int(value) if value is not None else 0) + delta
        await self.set(key, new_value)
        return new_value

    async def decrement(self, key: str, delta: int = 1) -> int:
        """Atomically decrement a numeric value by *delta*.

        If *key* does not exist it is treated as ``0`` before decrementing.

        Args:
            key: Key whose value to decrement.
            delta: Amount to subtract (default ``1``).

        Returns:
            The new integer value after decrementing.
        """
        # RU: Атомарно уменьшает числовое значение ключа на delta через increment(-delta).
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
