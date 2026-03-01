"""Bot interface for messaging platforms."""

from typing import Protocol, runtime_checkable, Any, Callable


@runtime_checkable
class IBot(Protocol):
    """
    Bot interface for regular bots (not userbots).
    
    Used for:
    - Telegram Bot API (aiogram, pyTelegramBotAPI)
    - Discord bots (discord.py)
    - Other bot platforms
    
    Note: This is a Protocol-based interface using structural subtyping.
    Implementations don't need to explicitly inherit from this class.
    """
    
    # ===== Lifecycle Management =====
    
    async def start(self) -> None:
        """Start the bot and establish connection."""
        ...
    
    async def stop(self) -> None:
        """Stop the bot and cleanup resources."""
        ...
    
    @property
    def is_running(self) -> bool:
        """Check if bot is currently running."""
        ...
    
    # ===== Basic Messaging =====
    
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
    
    async def delete_message(
        self, 
        chat_id: int | str, 
        message_id: int
    ) -> bool:
        """Delete a message."""
        ...
    
    # ===== Bot-Specific Features =====
    
    def command(self, commands: str | list[str]) -> Callable:
        """
        Decorator for registering command handlers.
        
        Args:
            commands: Command name(s) without leading slash
            
        Example:
            @bot.command("start")
            async def handle_start(message):
                await message.reply("Hello!")
        """
        ...
    
    def message_handler(self, **filters: Any) -> Callable:
        """
        Decorator for registering message handlers with filters.
        
        Args:
            **filters: Platform-specific filters (content_types, func, etc.)
        """
        ...
    
    async def delete_message(
        self, 
        chat_id: int | str, 
        message_id: int
    ) -> bool:
        """Delete a message."""
        ...


__all__ = [
    "IBot",
]
