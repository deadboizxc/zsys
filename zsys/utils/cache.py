"""Simple in-memory cache implementation."""
# RU: Простая реализация кэша в памяти с поддержкой TTL и потокобезопасности

import asyncio
import time
from typing import Any, Dict, Optional, Tuple


class MemoryCache:
    """
    Async-safe in-memory cache with TTL support.

    Uses asyncio.Lock for proper async concurrency.
    For sync-only code, use SyncMemoryCache instead.

    Example:
        cache = MemoryCache()
        await cache.set("user:123", user_data, ttl=3600)
        user = await cache.get("user:123")
    """

    # RU: Асинхронный кэш в памяти с блокировкой asyncio.Lock

    def __init__(self):
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """Get value by key. Returns None if not found or expired.

        Args:
            key: Cache key to look up.

        Returns:
            Cached value, or None if the key is missing or has expired.
        """
        # RU: Возвращает значение по ключу или None, если запись истекла или отсутствует
        async with self._lock:
            if key not in self._cache:
                return None

            value, expiry = self._cache[key]

            # Check if expired
            # RU: expiry == 0 означает «без ограничения»; положительное значение — метка времени истечения
            if expiry > 0 and time.time() > expiry:
                del self._cache[key]
                return None

            return value

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value with optional TTL (seconds).

        Args:
            key: Cache key
            value: Value to store
            ttl: Time to live in seconds. None or 0 for no expiry.

        Returns:
            True on success
        """
        # RU: Сохраняет значение в кэше с опциональным временем жизни
        async with self._lock:
            # RU: Если TTL не задан или равен 0, выставляем expiry=0 (бессрочно)
            expiry = time.time() + ttl if ttl else 0
            self._cache[key] = (value, expiry)
            return True

    async def delete(self, key: str) -> bool:
        """Delete key. Returns True if key existed.

        Args:
            key: Cache key to delete.

        Returns:
            True if the key existed and was removed, False otherwise.
        """
        # RU: Удаляет запись по ключу; возвращает True, если ключ существовал
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists and is not expired.

        Args:
            key: Cache key to check.

        Returns:
            True if the key exists and has not expired.
        """
        # RU: Проверяет наличие актуальной (не истёкшей) записи
        return await self.get(key) is not None

    async def clear(self) -> bool:
        """Clear all cached entries.

        Returns:
            True after clearing.
        """
        # RU: Очищает весь кэш атомарно под блокировкой
        async with self._lock:
            self._cache.clear()
            return True

    async def cleanup_expired(self) -> int:
        """Remove expired entries. Returns count of removed entries.

        Returns:
            Number of expired entries that were removed.
        """
        # RU: Удаляет все истёкшие записи и возвращает их количество
        async with self._lock:
            now = time.time()
            expired_keys = [
                key
                for key, (_, expiry) in self._cache.items()
                if expiry > 0 and now > expiry
            ]

            for key in expired_keys:
                del self._cache[key]

            return len(expired_keys)

    async def size(self) -> int:
        """Get number of entries in cache.

        Returns:
            Current number of entries (including not-yet-expired ones).
        """
        # RU: Возвращает текущее количество записей в кэше
        async with self._lock:
            return len(self._cache)


class SyncMemoryCache:
    """
    Thread-safe synchronous in-memory cache with TTL support.

    Uses threading.Lock. For async code, use MemoryCache instead.
    """

    # RU: Синхронный потокобезопасный кэш на основе threading.Lock

    def __init__(self):
        import threading

        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        """Get value by key.

        Args:
            key: Cache key to look up.

        Returns:
            Cached value, or None if the key is missing or has expired.
        """
        # RU: Возвращает значение по ключу или None при отсутствии или истечении TTL
        with self._lock:
            if key not in self._cache:
                return None

            value, expiry = self._cache[key]

            # RU: expiry == 0 означает «без ограничения»; положительное значение — метка времени истечения
            if expiry > 0 and time.time() > expiry:
                del self._cache[key]
                return None

            return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value with optional TTL.

        Args:
            key: Cache key.
            value: Value to store.
            ttl: Time to live in seconds. None or 0 for no expiry.

        Returns:
            True on success.
        """
        # RU: Сохраняет значение; вычисляет время истечения из TTL
        with self._lock:
            # RU: Если TTL не задан или равен 0, выставляем expiry=0 (бессрочно)
            expiry = time.time() + ttl if ttl else 0
            self._cache[key] = (value, expiry)
            return True

    def delete(self, key: str) -> bool:
        """Delete key.

        Args:
            key: Cache key to delete.

        Returns:
            True if the key existed and was removed, False otherwise.
        """
        # RU: Удаляет запись, если она существует
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> bool:
        """Clear all cache.

        Returns:
            True after clearing.
        """
        # RU: Полностью очищает внутренний словарь кэша
        with self._lock:
            self._cache.clear()
            return True


__all__ = ["MemoryCache", "SyncMemoryCache"]
