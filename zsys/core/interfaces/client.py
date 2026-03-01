"""Base client interface for messaging platforms."""

from typing import Protocol, runtime_checkable, Any


@runtime_checkable
class IClient(Protocol):
    """
    Base client interface.
    
    All bot and userbot clients must implement this interface.
    Provides lifecycle management and basic communication capabilities.
    """
    
    async def start(self) -> None:
        """Start the client and establish connection."""
        ...
    
    async def stop(self) -> None:
        """Stop the client and cleanup resources."""
        ...
    
    async def send_message(
        self, 
        chat_id: int | str, 
        text: str, 
        **kwargs: Any
    ) -> Any:
        """
        Send a text message to a chat.
        
        Args:
            chat_id: Target chat ID (int) or username (str)
            text: Message text
            **kwargs: Platform-specific parameters
            
        Returns:
            Message object (platform-specific)
        """
        ...
    
    @property
    def is_running(self) -> bool:
        """Check if client is currently running."""
        ...


__all__ = [
    "IClient",
]
