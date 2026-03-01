"""Storage interface for key-value storage backends."""

from typing import Protocol, runtime_checkable, Any, Optional


@runtime_checkable
class IStorage(Protocol):
    """
    Generic key-value storage interface.
    
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
    
    # ===== Connection Management =====
    
    async def connect(self) -> None:
        """Establish connection to storage."""
        ...
    
    async def disconnect(self) -> None:
        """Close connection to storage."""
        ...
    
    # ===== Basic Operations =====
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value by key.
        
        Returns:
            Value or None if key doesn't exist
        """
        ...
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        expire: int | None = None
    ) -> None:
        """
        Set key-value pair.
        
        Args:
            key: Storage key
            value: Value to store
            expire: Optional expiration time in seconds (for cache backends)
        """
        ...
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from storage.
        
        Returns:
            True if key was deleted, False if didn't exist
        """
        ...
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in storage."""
        ...
    
    async def clear(self) -> None:
        """Clear all data from storage."""
        ...
    
    async def keys(self, pattern: str = "*") -> list[str]:
        """
        Get all keys matching pattern.
        
        Args:
            pattern: Glob pattern (e.g., "user:*", "session:*")
        
        Returns:
            List of matching keys
        """
        ...
    
    # ===== Batch Operations =====
    
    async def mget(self, keys: list[str]) -> list[Optional[Any]]:
        """
        Get multiple values by keys.
        
        Args:
            keys: List of keys to retrieve
        
        Returns:
            List of values (None for non-existent keys)
        
        Example:
            values = await storage.mget(["key1", "key2", "key3"])
        """
        ...
    
    async def mset(self, mapping: dict[str, Any]) -> None:
        """
        Set multiple key-value pairs.
        
        Args:
            mapping: Dictionary of key-value pairs
        
        Example:
            await storage.mset({"key1": "val1", "key2": "val2"})
        """
        ...
    
    async def mdelete(self, keys: list[str]) -> int:
        """
        Delete multiple keys.
        
        Args:
            keys: List of keys to delete
        
        Returns:
            Number of keys that were deleted
        
        Example:
            deleted = await storage.mdelete(["key1", "key2", "key3"])
        """
        ...
    
    # ===== TTL Operations =====
    
    async def expire(self, key: str, seconds: int) -> bool:
        """
        Set expiration time for a key.
        
        Args:
            key: Storage key
            seconds: TTL in seconds
        
        Returns:
            True if timeout was set, False if key doesn't exist
        """
        ...
    
    async def ttl(self, key: str) -> int:
        """
        Get remaining time to live for a key.
        
        Args:
            key: Storage key
        
        Returns:
            TTL in seconds, -1 if no expiration, -2 if key doesn't exist
        """
        ...
    
    async def persist(self, key: str) -> bool:
        """
        Remove expiration from a key.
        
        Args:
            key: Storage key
        
        Returns:
            True if expiration was removed, False if key doesn't exist or has no expiration
        """
        ...
    
    # ===== Atomic Operations =====
    
    async def increment(self, key: str, delta: int = 1) -> int:
        """
        Increment numeric value by delta.
        
        Args:
            key: Storage key
            delta: Amount to increment (default: 1)
        
        Returns:
            New value after increment
        
        Example:
            count = await storage.increment("views")
            count = await storage.increment("score", 10)
        """
        ...
    
    async def decrement(self, key: str, delta: int = 1) -> int:
        """
        Decrement numeric value by delta.
        
        Args:
            key: Storage key
            delta: Amount to decrement (default: 1)
        
        Returns:
            New value after decrement
        """
        ...
    
    # ===== Metadata =====
    
    async def size(self) -> int:
        """
        Get number of keys in storage.
        
        Returns:
            Total number of keys
        """
        ...
    
    async def info(self) -> dict[str, Any]:
        """
        Get storage information and statistics.
        
        Returns:
            Dictionary with storage info (backend-specific)
        
        Example:
            info = await storage.info()
            print(f"Keys: {info.get('keys', 0)}")
            print(f"Memory: {info.get('memory_mb', 0)} MB")
        """
        ...


__all__ = [
    "IStorage",
]
