"""
BaseTransaction - Platform-agnostic transaction model.

Represents a blockchain transaction.
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from enum import Enum


class TransactionStatus(str, Enum):
    """Transaction status enumeration."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BaseTransaction:
    """
    Base transaction model for blockchain transactions.
    
    Can be extended by blockchain-specific implementations:
    - BitcoinTransaction
    - EthereumTransaction
    - SimpleChainTransaction
    """
    
    hash: str
    """Transaction hash (unique identifier)"""
    
    from_address: str
    """Sender address"""
    
    to_address: str
    """Recipient address"""
    
    amount: float
    """Transaction amount"""
    
    fee: float = 0.0
    """Transaction fee"""
    
    status: TransactionStatus = TransactionStatus.PENDING
    """Transaction status"""
    
    block_number: Optional[int] = None
    """Block number (if confirmed)"""
    
    confirmations: int = 0
    """Number of confirmations"""
    
    timestamp: datetime = field(default_factory=datetime.now)
    """When transaction was created"""
    
    confirmed_at: Optional[datetime] = None
    """When transaction was confirmed"""
    
    data: Optional[str] = None
    """Additional transaction data (smart contract calls, etc.)"""
    
    nonce: Optional[int] = None
    """Transaction nonce"""
    
    gas_price: Optional[float] = None
    """Gas price (for EVM chains)"""
    
    gas_limit: Optional[int] = None
    """Gas limit (for EVM chains)"""
    
    @property
    def is_pending(self) -> bool:
        """Check if transaction is pending."""
        return self.status == TransactionStatus.PENDING
    
    @property
    def is_confirmed(self) -> bool:
        """Check if transaction is confirmed."""
        return self.status == TransactionStatus.CONFIRMED
    
    @property
    def is_failed(self) -> bool:
        """Check if transaction failed."""
        return self.status == TransactionStatus.FAILED
    
    @property
    def total_cost(self) -> float:
        """Get total cost (amount + fee)."""
        return self.amount + self.fee
    
    @property
    def display_hash(self) -> str:
        """Get shortened hash for display (first 8 + last 6 chars)."""
        if len(self.hash) > 20:
            return f"{self.hash[:8]}...{self.hash[-6:]}"
        return self.hash
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "hash": self.hash,
            "from_address": self.from_address,
            "to_address": self.to_address,
            "amount": self.amount,
            "fee": self.fee,
            "status": self.status.value,
            "block_number": self.block_number,
            "confirmations": self.confirmations,
            "timestamp": self.timestamp.isoformat(),
            "confirmed_at": self.confirmed_at.isoformat() if self.confirmed_at else None,
            "data": self.data,
            "nonce": self.nonce,
            "gas_price": self.gas_price,
            "gas_limit": self.gas_limit,
        }
