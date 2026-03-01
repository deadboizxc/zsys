"""
BaseWallet - Platform-agnostic wallet model.

Represents a cryptocurrency wallet.
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class BaseWallet:
    """
    Base wallet model for cryptocurrency wallets.
    
    Can be extended by blockchain-specific implementations:
    - BitcoinWallet
    - EthereumWallet
    - SimpleChainWallet
    """
    
    address: str
    """Wallet address (public key)"""
    
    private_key: str
    """Private key (handle with care!)"""
    
    balance: float = 0.0
    """Current wallet balance"""
    
    currency: str = "BTC"
    """Currency type (BTC, ETH, etc.)"""
    
    label: Optional[str] = None
    """Wallet label/name"""
    
    is_watch_only: bool = False
    """Whether this is a watch-only wallet (no private key access)"""
    
    created_at: datetime = field(default_factory=datetime.now)
    """When this wallet was created"""
    
    last_updated: datetime = field(default_factory=datetime.now)
    """When balance was last updated"""
    
    @property
    def display_address(self) -> str:
        """Get shortened address for display (first 8 + last 6 chars)."""
        if len(self.address) > 20:
            return f"{self.address[:8]}...{self.address[-6:]}"
        return self.address
    
    @property
    def has_balance(self) -> bool:
        """Check if wallet has non-zero balance."""
        return self.balance > 0
    
    def to_dict(self, include_private_key: bool = False) -> dict:
        """
        Convert to dictionary.
        
        Args:
            include_private_key: Whether to include private key (default: False)
        """
        data = {
            "address": self.address,
            "balance": self.balance,
            "currency": self.currency,
            "label": self.label,
            "is_watch_only": self.is_watch_only,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
        }
        
        if include_private_key and not self.is_watch_only:
            data["private_key"] = self.private_key
        
        return data
