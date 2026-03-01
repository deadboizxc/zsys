"""Blockchain interface."""

from typing import Protocol, runtime_checkable, Any, Optional


@runtime_checkable
class IBlockchain(Protocol):
    """
    Blockchain interface.
    
    Can be implemented by:
    - Simple blockchain (educational/demo)
    - EVM chains (Ethereum, BSC, Polygon)
    - Bitcoin
    - Other blockchain networks
    """
    
    def add_block(self, data: Any) -> Any:
        """
        Add a new block to the chain.
        
        Args:
            data: Block data (transactions, etc.)
            
        Returns:
            Created block
        """
        ...
    
    def validate_chain(self) -> bool:
        """
        Validate the entire blockchain.
        
        Returns:
            True if chain is valid, False otherwise
        """
        ...
    
    def get_balance(self, address: str) -> float:
        """
        Get balance for an address.
        
        Args:
            address: Wallet address
            
        Returns:
            Balance amount
        """
        ...
    
    def get_block(self, index: int) -> Optional[Any]:
        """
        Get block by index.
        
        Args:
            index: Block index
            
        Returns:
            Block or None if not found
        """
        ...
    
    @property
    def chain(self) -> list[Any]:
        """Get the entire blockchain."""
        ...
    
    @property
    def latest_block(self) -> Any:
        """Get the latest block."""
        ...


__all__ = [
    "IBlockchain",
]
