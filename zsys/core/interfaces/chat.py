"""Chat interface for messaging platforms."""

from typing import Protocol, runtime_checkable, Any
from enum import Enum


class ChatType(str, Enum):
    """Chat type enumeration."""
    PRIVATE = "private"
    GROUP = "group"
    SUPERGROUP = "supergroup"
    CHANNEL = "channel"
    BOT = "bot"


@runtime_checkable
class IChat(Protocol):
    """
    Chat interface for messaging platforms.
    
    Represents any conversation: private, group, channel, etc.
    Platform-agnostic abstraction.
    """
    
    @property
    def id(self) -> int:
        """Chat ID (unique identifier)."""
        ...
    
    @property
    def title(self) -> str | None:
        """Chat title (for groups/channels, None for private chats)."""
        ...
    
    @property
    def type(self) -> ChatType:
        """Chat type (private, group, channel, etc.)."""
        ...
    
    @property
    def username(self) -> str | None:
        """Chat username (if exists)."""
        ...
    
    async def send_message(self, text: str, **kwargs: Any) -> Any:
        """Send a message to this chat."""
        ...
    
    async def get_member(self, user_id: int) -> Any:
        """Get chat member information."""
        ...
    
    async def get_members_count(self) -> int:
        """Get total members count."""
        ...


__all__ = [
    "IChat",
    "ChatType",
]
