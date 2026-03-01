"""Wallet interface for cryptocurrency wallets."""

from typing import Protocol, runtime_checkable, Any, Optional


@runtime_checkable
class IWallet(Protocol):
    """
    Crypto wallet interface.
    
    Can be implemented by:
    - Bitcoin wallet
    - Ethereum wallet
    - Multi-coin wallets
    - Hardware wallet integrations
    """
    
    @property
    def address(self) -> str:
        """Get wallet address (public key)."""
        ...
    
    @property
    def private_key(self) -> str:
        """
        Get wallet private key.
        
        WARNING: Handle with extreme care!
        """
        ...
    
    @property
    def balance(self) -> float:
        """Get current wallet balance."""
        ...
    
    def create_transaction(
        self,
        to: str,
        amount: float,
        **kwargs: Any
    ) -> Any:
        """
        Create a new transaction.
        
        Args:
            to: Recipient address
            amount: Amount to send
            **kwargs: Additional parameters (gas, nonce, etc.)
            
        Returns:
            Transaction object
        """
        ...
    
    def sign_transaction(self, transaction: Any) -> Any:
        """
        Sign a transaction with wallet's private key.
        
        Args:
            transaction: Transaction to sign
            
        Returns:
            Signed transaction
        """
        ...
    
    async def send_transaction(self, transaction: Any) -> str:
        """
        Send a signed transaction to the network.
        
        Args:
            transaction: Signed transaction
            
        Returns:
            Transaction hash
        """
        ...
    
    async def get_transaction(self, tx_hash: str) -> Optional[Any]:
        """
        Get transaction by hash.
        
        Args:
            tx_hash: Transaction hash
            
        Returns:
            Transaction object or None
        """
        ...


__all__ = [
    "IWallet",
]
