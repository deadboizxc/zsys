"""
Example: Storage Comparison

This example demonstrates different storage backends:
- MemoryStorage (fast, non-persistent)
- SQLiteStorage (persistent, file-based)
- RedisStorage (fast, persistent, requires Redis server)

Install:
    pip install zsys[storage]

Run:
    python examples/storage_example.py
"""

import asyncio
from zsys.storage.memory import MemoryStorage
from zsys.storage.sqlite import SQLiteStorage
from zsys.storage.redis import RedisStorage
from zsys.core.logging import get_logger

logger = get_logger(__name__)


async def test_storage(storage, name: str):
    """Test storage operations."""
    logger.info(f"\n=== Testing {name} ===")
    
    # Connect
    await storage.connect()
    logger.info(f"✅ Connected to {name}")
    
    # Set values
    await storage.set("user:1", {"name": "Alice", "age": 25})
    await storage.set("user:2", {"name": "Bob", "age": 30})
    await storage.set("counter", 0)
    logger.info("✅ Set 3 key-value pairs")
    
    # Get values
    user1 = await storage.get("user:1")
    user2 = await storage.get("user:2")
    logger.info(f"  user:1 = {user1}")
    logger.info(f"  user:2 = {user2}")
    
    # Check existence
    exists = await storage.exists("user:1")
    not_exists = await storage.exists("user:999")
    logger.info(f"✅ user:1 exists: {exists}, user:999 exists: {not_exists}")
    
    # Get all keys
    keys = await storage.keys("user:*")
    logger.info(f"✅ Keys matching 'user:*': {keys}")
    
    # Update value
    counter = await storage.get("counter")
    counter += 1
    await storage.set("counter", counter)
    logger.info(f"✅ Updated counter: {counter}")
    
    # Delete value
    deleted = await storage.delete("user:2")
    logger.info(f"✅ Deleted user:2: {deleted}")
    
    # Get remaining keys
    remaining_keys = await storage.keys()
    logger.info(f"✅ Remaining keys: {remaining_keys}")
    
    # Clear all
    await storage.clear()
    logger.info(f"✅ Cleared all data")
    
    # Disconnect
    await storage.disconnect()
    logger.info(f"✅ Disconnected from {name}")


async def main():
    """Main function."""
    logger.info("=== Storage Backends Comparison ===\n")
    
    # Test MemoryStorage
    memory_storage = MemoryStorage()
    await test_storage(memory_storage, "MemoryStorage")
    
    # Test SQLiteStorage
    sqlite_storage = SQLiteStorage("test_storage.db")
    await test_storage(sqlite_storage, "SQLiteStorage")
    
    # Test RedisStorage (if available)
    try:
        redis_storage = RedisStorage("redis://localhost:6379/0")
        await test_storage(redis_storage, "RedisStorage")
    except Exception as e:
        logger.warning(f"⚠️ RedisStorage not available: {e}")
        logger.info("  Make sure Redis server is running:")
        logger.info("  docker run -d -p 6379:6379 redis:alpine")
    
    logger.info("\n✅ All storage tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
