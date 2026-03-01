"""
Tests for Core Interfaces

These tests verify that core interfaces follow Protocol pattern correctly.
"""

import pytest
from typing import Protocol
from zsys.core.interfaces import (
    IClient,
    IBot,
    IUserBot,
    IChat,
    IStorage,
    ICipher,
    IBlockchain,
    IWallet,
)


def test_iclient_is_protocol():
    """Test that IClient is a Protocol."""
    assert isinstance(IClient, type)
    
    # Check runtime_checkable
    from typing import runtime_checkable
    assert hasattr(IClient, '__protocol_attrs__')


def test_ibot_is_protocol():
    """Test that IBot is a Protocol."""
    assert isinstance(IBot, type)
    

def test_iuserbot_is_protocol():
    """Test that IUserBot is a Protocol."""
    assert isinstance(IUserBot, type)


def test_ichat_is_protocol():
    """Test that IChat is a Protocol."""
    assert isinstance(IChat, type)


def test_istorage_is_protocol():
    """Test that IStorage is a Protocol."""
    assert isinstance(IStorage, type)


def test_icipher_is_protocol():
    """Test that ICipher is a Protocol."""
    assert isinstance(ICipher, type)


def test_iblockchain_is_protocol():
    """Test that IBlockchain is a Protocol."""
    assert isinstance(IBlockchain, type)


def test_iwallet_is_protocol():
    """Test that IWallet is a Protocol."""
    assert isinstance(IWallet, type)


# Test that mock classes can implement protocols without inheritance
class MockClient:
    """Mock client for testing Protocol pattern."""
    
    async def start(self) -> None:
        pass
    
    async def stop(self) -> None:
        pass
    
    async def send_message(self, chat_id, text, **kwargs):
        return None
    
    @property
    def is_running(self) -> bool:
        return True


def test_protocol_works_without_inheritance():
    """Test that Protocol pattern works without explicit inheritance."""
    mock = MockClient()
    
    # Should not raise TypeError
    assert isinstance(mock, IClient)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
