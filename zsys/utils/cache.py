"""Simple in-memory cache implementation."""

import asyncio
import time
from typing import Optional, Any, Dict, Tuple


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
    
    def __init__(self):
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value by key. Returns None if not found or expired."""
        async with self._lock:
            if key not in self._cache:
                return None
            
            value, expiry = self._cache[key]
            
            # Check if expired
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
        async with self._lock:
            expiry = time.time() + ttl if ttl else 0
            self._cache[key] = (value, expiry)
            return True
    
    async def delete(self, key: str) -> bool:
        """Delete key. Returns True if key existed."""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        return await self.get(key) is not None
    
    async def clear(self) -> bool:
        """Clear all cached entries."""
        async with self._lock:
            self._cache.clear()
            return True
    
    async def cleanup_expired(self) -> int:
        """Remove expired entries. Returns count of removed entries."""
        async with self._lock:
            now = time.time()
            expired_keys = [
                key for key, (_, expiry) in self._cache.items()
                if expiry > 0 and now > expiry
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            return len(expired_keys)
    
    async def size(self) -> int:
        """Get number of entries in cache."""
        async with self._lock:
            return len(self._cache)


class SyncMemoryCache:
    """
    Thread-safe synchronous in-memory cache with TTL support.
    
    Uses threading.Lock. For async code, use MemoryCache instead.
    """
    
    def __init__(self):
        import threading
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value by key."""
        with self._lock:
            if key not in self._cache:
                return None
            
            value, expiry = self._cache[key]
            
            if expiry > 0 and time.time() > expiry:
                del self._cache[key]
                return None
            
            return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value with optional TTL."""
        with self._lock:
            expiry = time.time() + ttl if ttl else 0
            self._cache[key] = (value, expiry)
            return True
    
    def delete(self, key: str) -> bool:
        """Delete key."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> bool:
        """Clear all cache."""
        with self._lock:
            self._cache.clear()
            return True


__all__ = ['MemoryCache', 'SyncMemoryCache']
