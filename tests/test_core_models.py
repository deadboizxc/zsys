"""
Tests for Core Models

These tests verify that core models work correctly.
"""

import pytest
from datetime import datetime
from zsys.core.dataclass_models import (
    BaseUser,
    BaseChat,
    BaseClient,
    BaseMessage,
    BaseWallet,
    BaseTransaction,
)
from zsys.core.interfaces.chat import ChatType
from zsys.core.dataclass_models.base_client import ClientStatus
from zsys.core.dataclass_models.base_message import MessageType
from zsys.core.dataclass_models.base_transaction import TransactionStatus


def test_base_user():
    """Test BaseUser model."""
    user = BaseUser(
        id=123,
        username="testuser",
        first_name="Test",
        last_name="User"
    )
    
    assert user.id == 123
    assert user.username == "testuser"
    assert user.full_name == "Test User"
    assert user.mention == "@testuser"
    assert not user.is_bot
    
    # Test to_dict
    user_dict = user.to_dict()
    assert user_dict["id"] == 123
    assert user_dict["username"] == "testuser"


def test_base_chat():
    """Test BaseChat model."""
    chat = BaseChat(
        id=456,
        type=ChatType.GROUP,
        title="Test Group"
    )
    
    assert chat.id == 456
    assert chat.type == ChatType.GROUP
    assert chat.is_group
    assert not chat.is_private
    assert chat.display_name == "Test Group"


def test_base_client():
    """Test BaseClient model."""
    client = BaseClient(
        name="test_client",
        token="test_token"
    )
    
    assert client.name == "test_client"
    assert client.is_bot
    assert not client.is_userbot
    assert not client.is_running
    assert client.status == ClientStatus.IDLE


def test_base_message():
    """Test BaseMessage model."""
    message = BaseMessage(
        id=789,
        chat_id=456,
        from_user_id=123,
        text="Hello, world!"
    )
    
    assert message.id == 789
    assert message.chat_id == 456
    assert message.text == "Hello, world!"
    assert message.is_text
    assert not message.is_media
    assert not message.is_reply


def test_base_wallet():
    """Test BaseWallet model."""
    wallet = BaseWallet(
        address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        private_key="secret_key",
        balance=1.5,
        currency="ETH"
    )
    
    assert wallet.address.startswith("0x")
    assert wallet.currency == "ETH"
    assert wallet.has_balance
    assert not wallet.is_watch_only
    
    # Test to_dict without private key
    wallet_dict = wallet.to_dict(include_private_key=False)
    assert "private_key" not in wallet_dict
    assert wallet_dict["balance"] == 1.5


def test_base_transaction():
    """Test BaseTransaction model."""
    tx = BaseTransaction(
        hash="0xabc123",
        from_address="0xFrom",
        to_address="0xTo",
        amount=1.0,
        fee=0.001
    )
    
    assert tx.hash == "0xabc123"
    assert tx.is_pending
    assert not tx.is_confirmed
    assert tx.total_cost == 1.001
    
    # Test status change
    tx.status = TransactionStatus.CONFIRMED
    assert tx.is_confirmed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
