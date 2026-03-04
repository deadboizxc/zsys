"""SimpleBlockchain — educational proof-of-work blockchain.

Provides a self-contained blockchain implementation for learning and
demonstration purposes.  Implements IBlockchain with SHA-256 hashing
and configurable proof-of-work difficulty.
"""
# RU: SimpleBlockchain — учебный блокчейн с доказательством работы.
# RU: Реализует IBlockchain: PoW, валидация цепи, расчёт баланса.

from typing import Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import json
from zsys.core.interfaces import IBlockchain
from zsys.log import get_logger


logger = get_logger(__name__)


@dataclass
class Block:
    """Individual block in the blockchain chain.

    Attributes:
        index: Zero-based position in the chain.
        timestamp: When this block was created.
        data: Arbitrary payload (transactions, strings, etc.).
        previous_hash: Hash of the preceding block.
        nonce: Proof-of-work counter incremented during mining.
        hash: SHA-256 hash of this block's contents.
    """

    # RU: Блок в цепочке блоков.

    index: int
    timestamp: datetime
    data: Any
    previous_hash: str
    nonce: int = 0
    hash: str = ""

    def calculate_hash(self) -> str:
        """Calculate block hash."""
        block_string = json.dumps(
            {
                "index": self.index,
                "timestamp": self.timestamp.isoformat(),
                "data": self.data,
                "previous_hash": self.previous_hash,
                "nonce": self.nonce,
            },
            sort_keys=True,
        )

        return hashlib.sha256(block_string.encode()).hexdigest()

    def mine_block(self, difficulty: int = 4) -> None:
        """Mine block with proof-of-work."""
        target = "0" * difficulty

        while not self.hash.startswith(target):
            self.nonce += 1
            self.hash = self.calculate_hash()

        logger.info(f"Block mined: {self.hash} (nonce: {self.nonce})")


class SimpleBlockchain(IBlockchain):
    """
    Simple blockchain implementation.

    Features:
    - Proof of Work mining
    - Block validation
    - Transaction tracking
    - Balance calculation

    Usage:
        blockchain = SimpleBlockchain(difficulty=4)

        # Add blocks
        blockchain.add_block({"from": "Alice", "to": "Bob", "amount": 50})
        blockchain.add_block({"from": "Bob", "to": "Charlie", "amount": 25})

        # Validate chain
        is_valid = blockchain.validate_chain()

        # Get balance
        balance = blockchain.get_balance("Alice")
    """

    # RU: Учебный блокчейн с PoW, валидацией и расчётом баланса.

    def __init__(self, difficulty: int = 4):
        """
        Initialize blockchain.

        Args:
            difficulty: Mining difficulty (number of leading zeros)
        """
        self.difficulty = difficulty
        self._chain: List[Block] = []
        self._create_genesis_block()

    def _create_genesis_block(self) -> None:
        """Create the first block (genesis block)."""
        genesis = Block(
            index=0, timestamp=datetime.now(), data="Genesis Block", previous_hash="0"
        )
        genesis.hash = genesis.calculate_hash()
        self._chain.append(genesis)
        logger.info("Genesis block created")

    def add_block(self, data: Any) -> Block:
        """
        Add a new block to the chain.

        Args:
            data: Block data (transactions, etc.)

        Returns:
            Created block
        """
        previous_block = self._chain[-1]

        new_block = Block(
            index=len(self._chain),
            timestamp=datetime.now(),
            data=data,
            previous_hash=previous_block.hash,
        )

        new_block.mine_block(self.difficulty)
        self._chain.append(new_block)

        logger.info(f"Block {new_block.index} added to chain")
        return new_block

    def validate_chain(self) -> bool:
        """
        Validate the entire blockchain.

        Returns:
            True if chain is valid, False otherwise
        """
        for i in range(1, len(self._chain)):
            current_block = self._chain[i]
            previous_block = self._chain[i - 1]

            # Check hash
            if current_block.hash != current_block.calculate_hash():
                logger.error(f"Block {i} has invalid hash")
                return False

            # Check previous hash link
            if current_block.previous_hash != previous_block.hash:
                logger.error(f"Block {i} has invalid previous hash")
                return False

        logger.info("Blockchain is valid")
        return True

    def get_balance(self, address: str) -> float:
        """
        Get balance for an address.

        Args:
            address: Wallet address

        Returns:
            Balance amount
        """
        balance = 0.0

        for block in self._chain[1:]:  # Skip genesis block
            data = block.data

            if isinstance(data, dict):
                if data.get("from") == address:
                    balance -= data.get("amount", 0)

                if data.get("to") == address:
                    balance += data.get("amount", 0)

        return balance

    def get_block(self, index: int) -> Optional[Block]:
        """
        Get block by index.

        Args:
            index: Block index

        Returns:
            Block or None if not found
        """
        if 0 <= index < len(self._chain):
            return self._chain[index]
        return None

    @property
    def chain(self) -> List[Block]:
        """Get the entire blockchain."""
        return self._chain

    @property
    def latest_block(self) -> Block:
        """Get the latest block."""
        return self._chain[-1]

    def to_dict(self) -> dict:
        """Convert blockchain to dictionary."""
        return {
            "length": len(self._chain),
            "difficulty": self.difficulty,
            "is_valid": self.validate_chain(),
            "blocks": [
                {
                    "index": block.index,
                    "timestamp": block.timestamp.isoformat(),
                    "data": block.data,
                    "hash": block.hash,
                    "previous_hash": block.previous_hash,
                    "nonce": block.nonce,
                }
                for block in self._chain
            ],
        }


__all__ = ["SimpleBlockchain", "Block"]
