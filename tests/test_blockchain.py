"""
Tests for Blockchain implementations.
"""

import pytest
from zsys.blockchain.simple_chain import SimpleBlockchain, Block


def test_simple_blockchain_creation():
    """Test SimpleBlockchain initialization."""
    blockchain = SimpleBlockchain(difficulty=2)
    
    assert len(blockchain.chain) == 1  # Genesis block
    assert blockchain.chain[0].index == 0
    assert blockchain.chain[0].data == "Genesis Block"
    assert blockchain.difficulty == 2


def test_add_block():
    """Test adding blocks to blockchain."""
    blockchain = SimpleBlockchain(difficulty=2)
    
    # Add block
    block = blockchain.add_block({"from": "Alice", "to": "Bob", "amount": 50})
    
    assert block.index == 1
    assert block.data == {"from": "Alice", "to": "Bob", "amount": 50}
    assert block.hash.startswith("00")  # Difficulty 2


def test_validate_chain():
    """Test blockchain validation."""
    blockchain = SimpleBlockchain(difficulty=2)
    
    # Add blocks
    blockchain.add_block({"from": "Alice", "to": "Bob", "amount": 50})
    blockchain.add_block({"from": "Bob", "to": "Charlie", "amount": 25})
    
    # Should be valid
    assert blockchain.validate_chain() is True
    
    # Tamper with block
    blockchain.chain[1].data = {"from": "Hacker", "to": "Hacker", "amount": 9999}
    
    # Should be invalid
    assert blockchain.validate_chain() is False


def test_get_balance():
    """Test balance calculation."""
    blockchain = SimpleBlockchain(difficulty=2)
    
    # Add transactions
    blockchain.add_block({"from": "Alice", "to": "Bob", "amount": 50})
    blockchain.add_block({"from": "Bob", "to": "Charlie", "amount": 25})
    blockchain.add_block({"from": "Alice", "to": "Charlie", "amount": 30})
    
    # Check balances
    assert blockchain.get_balance("Alice") == -80  # -50 - 30
    assert blockchain.get_balance("Bob") == 25  # +50 - 25
    assert blockchain.get_balance("Charlie") == 55  # +25 + 30


def test_get_block():
    """Test getting block by index."""
    blockchain = SimpleBlockchain(difficulty=2)
    
    blockchain.add_block({"test": "data"})
    
    # Get genesis block
    genesis = blockchain.get_block(0)
    assert genesis.index == 0
    
    # Get second block
    block = blockchain.get_block(1)
    assert block.index == 1
    assert block.data == {"test": "data"}
    
    # Non-existent block
    none_block = blockchain.get_block(999)
    assert none_block is None


def test_latest_block():
    """Test getting latest block."""
    blockchain = SimpleBlockchain(difficulty=2)
    
    # Latest should be genesis
    assert blockchain.latest_block.index == 0
    
    # Add block
    blockchain.add_block({"test": "data"})
    
    # Latest should be new block
    assert blockchain.latest_block.index == 1


def test_to_dict():
    """Test blockchain to dictionary conversion."""
    blockchain = SimpleBlockchain(difficulty=2)
    blockchain.add_block({"test": "data"})
    
    blockchain_dict = blockchain.to_dict()
    
    assert blockchain_dict["length"] == 2
    assert blockchain_dict["difficulty"] == 2
    assert blockchain_dict["is_valid"] is True
    assert len(blockchain_dict["blocks"]) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
