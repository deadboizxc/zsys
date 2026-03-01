"""
BaseChat - Platform-agnostic chat model.

Represents any conversation: private, group, channel, etc.
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from enum import Enum


# TODO: Move to core.interfaces.chat when interfaces module is created
class ChatType(str, Enum):
    """Chat type enumeration."""
    PRIVATE = "private"
    GROUP = "group"
    SUPERGROUP = "supergroup"
    CHANNEL = "channel"
    BOT = "bot"


@dataclass
class BaseChat:
    """
    Base chat model for all platforms.
    
    Can be extended by platform-specific implementations:
    - TelegramChat
    - DiscordChannel
    - WebChatRoom
    """
    
    id: int
    """Unique chat ID"""
    
    type: ChatType
    """Chat type (private, group, channel, etc.)"""
    
    title: Optional[str] = None
    """Chat title (for groups/channels)"""
    
    username: Optional[str] = None
    """Chat username (if public)"""
    
    description: Optional[str] = None
    """Chat description"""
    
    members_count: Optional[int] = None
    """Total members count"""
    
    is_verified: bool = False
    """Whether this chat is verified"""
    
    is_restricted: bool = False
    """Whether this chat is restricted"""
    
    created_at: datetime = field(default_factory=datetime.now)
    """When this chat record was created"""
    
    @property
    def is_private(self) -> bool:
        """Check if this is a private chat."""
        return self.type == ChatType.PRIVATE
    
    @property
    def is_group(self) -> bool:
        """Check if this is a group chat."""
        return self.type in (ChatType.GROUP, ChatType.SUPERGROUP)
    
    @property
    def is_channel(self) -> bool:
        """Check if this is a channel."""
        return self.type == ChatType.CHANNEL
    
    @property
    def display_name(self) -> str:
        """Get display name (title or username or ID)."""
        if self.title:
            return self.title
        elif self.username:
            return f"@{self.username}"
        return f"Chat {self.id}"
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "title": self.title,
            "username": self.username,
            "description": self.description,
            "members_count": self.members_count,
            "is_verified": self.is_verified,
            "is_restricted": self.is_restricted,
            "created_at": self.created_at.isoformat(),
        }
