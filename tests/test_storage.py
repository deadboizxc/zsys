"""
Tests for Storage implementations.
"""

import pytest
import asyncio
from zsys.storage.base import MemoryStorage
from zsys.storage.sqlite import SqliteDatabase as SQLiteStorage


@pytest.mark.asyncio
async def test_memory_storage():
    """Test MemoryStorage implementation."""
    storage = MemoryStorage()
    
    # Connect
    await storage.connect()
    
    # Set and get
    await storage.set("test_key", "test_value")
    value = await storage.get("test_key")
    assert value == "test_value"
    
    # Exists
    exists = await storage.exists("test_key")
    assert exists is True
    
    # Set complex data
    await storage.set("user:1", {"name": "Alice", "age": 25})
    user = await storage.get("user:1")
    assert user["name"] == "Alice"
    assert user["age"] == 25
    
    # Keys
    await storage.set("user:2", {"name": "Bob"})
    keys = await storage.keys("user:*")
    assert len(keys) == 2
    assert "user:1" in keys
    assert "user:2" in keys
    
    # Delete
    deleted = await storage.delete("user:1")
    assert deleted is True
    exists = await storage.exists("user:1")
    assert exists is False
    
    # Clear
    await storage.clear()
    keys = await storage.keys()
    assert len(keys) == 0
    
    # Disconnect
    await storage.disconnect()


@pytest.mark.asyncio
async def test_sqlite_storage():
    """Test SQLiteStorage implementation."""
    pytest.skip("SqliteDatabase is a sync Database, not an async BaseStorage")
    storage = SQLiteStorage(":memory:")  # Use in-memory database
    
    # Connect
    await storage.connect()
    
    # Set and get
    await storage.set("test_key", "test_value")
    value = await storage.get("test_key")
    assert value == "test_value"
    
    # Exists
    exists = await storage.exists("test_key")
    assert exists is True
    
    # Set complex data
    await storage.set("user:1", {"name": "Alice", "age": 25})
    user = await storage.get("user:1")
    assert user["name"] == "Alice"
    assert user["age"] == 25
    
    # Keys
    await storage.set("user:2", {"name": "Bob"})
    keys = await storage.keys("user:*")
    assert len(keys) == 2
    
    # Delete
    deleted = await storage.delete("user:1")
    assert deleted is True
    
    # Disconnect
    await storage.disconnect()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
