"""IStorage — generic key-value storage interface.

Defines the contract for all pluggable storage backends (SQLite, Redis,
in-memory, etc.).  Implementations must support CRUD, batch ops, TTL
management, and atomic increment/decrement.
"""
# RU: Интерфейс IStorage — обобщённое хранилище ключ-значение.
# RU: Все бэкенды (SQLite, Redis, память и др.) должны реализовать этот контракт.

from typing import Any, Optional, Protocol, runtime_checkable


@runtime_checkable
class IStorage(Protocol):
    """Generic key-value storage interface.

    Can be implemented by:
    - SQLite (persistent storage)
    - Redis (cache, sessions)
    - Memory (temporary storage)
    - PostgreSQL (relational data)

    Features:
    - Basic CRUD operations (get, set, delete)
    - Batch operations (mget, mset, mdelete)
    - TTL management (expire, ttl, persist)
    - Atomic operations (increment, decrement)
    - Pattern matching (keys)
    - Metadata (size, info)
    """

    # RU: Интерфейс обобщённого хранилища ключ-значение.

    # ===== Connection Management =====

    async def connect(self) -> None:
        """Establish connection to storage."""
        # RU: Установить соединение с хранилищем.
        ...

    async def disconnect(self) -> None:
        """Close connection to storage."""
        # RU: Закрыть соединение с хранилищем.
        ...

    # ===== Basic Operations =====

    async def get(self, key: str) -> Optional[Any]:
        """Get value by key.

        Returns:
            Value or None if key does not exist in the store.
        """
        # RU: Получить значение по ключу. Возвращает None, если ключ отсутствует.
        ...

    async def set(self, key: str, value: Any, expire: int | None = None) -> None:
        """Set key-value pair.

        Args:
            key: Storage key.
            value: Value to store.
            expire: Optional expiration time in seconds (for cache backends).
        """
        # RU: Сохранить пару «ключ–значение» с необязательным временем жизни.
        ...

    async def delete(self, key: str) -> bool:
        """Delete key from storage.

        Returns:
            True if key was deleted, False if it did not exist.
        """
        # RU: Удалить ключ. Возвращает True, если ключ был удалён.
        ...

    async def exists(self, key: str) -> bool:
        """Check if key exists in storage."""
        # RU: Проверить наличие ключа в хранилище.
        ...

    async def clear(self) -> None:
        """Clear all data from storage."""
        # RU: Очистить все данные из хранилища.
        ...

    async def keys(self, pattern: str = "*") -> list[str]:
        """Get all keys matching pattern.

        Args:
            pattern: Glob pattern (e.g., "user:*", "session:*").

        Returns:
            List of matching keys.
        """
        # RU: Получить список ключей, совпадающих с шаблоном (glob).
        ...

    # ===== Batch Operations =====

    async def mget(self, keys: list[str]) -> list[Optional[Any]]:
        """Get multiple values by keys.

        Args:
            keys: List of keys to retrieve.

        Returns:
            List of values (None for non-existent keys).

        Example:
            values = await storage.mget(["key1", "key2", "key3"])
        """
        # RU: Получить несколько значений по списку ключей.
        ...

    async def mset(self, mapping: dict[str, Any]) -> None:
        """Set multiple key-value pairs.

        Args:
            mapping: Dictionary of key-value pairs.

        Example:
            await storage.mset({"key1": "val1", "key2": "val2"})
        """
        # RU: Сохранить несколько пар «ключ–значение» за одну операцию.
        ...

    async def mdelete(self, keys: list[str]) -> int:
        """Delete multiple keys.

        Args:
            keys: List of keys to delete.

        Returns:
            Number of keys that were actually deleted.

        Example:
            deleted = await storage.mdelete(["key1", "key2", "key3"])
        """
        # RU: Удалить несколько ключей. Возвращает количество фактически удалённых.
        ...

    # ===== TTL Operations =====

    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration time for a key.

        Args:
            key: Storage key.
            seconds: TTL in seconds.

        Returns:
            True if timeout was set, False if key does not exist.
        """
        # RU: Установить время жизни для ключа в секундах.
        ...

    async def ttl(self, key: str) -> int:
        """Get remaining time to live for a key.

        Args:
            key: Storage key.

        Returns:
            TTL in seconds; -1 if no expiration is set; -2 if key does not exist.
        """
        # RU: Получить оставшееся время жизни ключа (-1 — без TTL, -2 — ключ отсутствует).
        ...

    async def persist(self, key: str) -> bool:
        """Remove expiration from a key.

        Args:
            key: Storage key.

        Returns:
            True if expiration was removed, False if key does not exist or has no expiration.
        """
        # RU: Снять TTL с ключа, сделав его постоянным.
        ...

    # ===== Atomic Operations =====

    async def increment(self, key: str, delta: int = 1) -> int:
        """Increment numeric value by delta.

        Args:
            key: Storage key.
            delta: Amount to increment (default: 1).

        Returns:
            New value after increment.

        Example:
            count = await storage.increment("views")
            count = await storage.increment("score", 10)
        """
        # RU: Атомарно увеличить числовое значение ключа на delta.
        ...

    async def decrement(self, key: str, delta: int = 1) -> int:
        """Decrement numeric value by delta.

        Args:
            key: Storage key.
            delta: Amount to decrement (default: 1).

        Returns:
            New value after decrement.
        """
        # RU: Атомарно уменьшить числовое значение ключа на delta.
        ...

    # ===== Metadata =====

    async def size(self) -> int:
        """Get number of keys in storage.

        Returns:
            Total number of keys.
        """
        # RU: Получить общее количество ключей в хранилище.
        ...

    async def info(self) -> dict[str, Any]:
        """Get storage information and statistics.

        Returns:
            Dictionary with storage info (backend-specific).

        Example:
            info = await storage.info()
            print(f"Keys: {info.get('keys', 0)}")
            print(f"Memory: {info.get('memory_mb', 0)} MB")
        """
        # RU: Получить информацию и статистику хранилища (зависит от бэкенда).
        ...


__all__ = [
    "IStorage",
]
