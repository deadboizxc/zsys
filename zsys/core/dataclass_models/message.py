"""
BaseMessage - Platform-agnostic message model.

Represents a message in any messaging platform.
"""

from dataclasses import dataclass, field
from typing import Optional, Any
from datetime import datetime
from enum import Enum


class MessageType(str, Enum):
    """Message type enumeration."""
    TEXT = "text"
    PHOTO = "photo"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    VOICE = "voice"
    STICKER = "sticker"
    ANIMATION = "animation"
    LOCATION = "location"
    CONTACT = "contact"
    POLL = "poll"
    SERVICE = "service"


@dataclass
class BaseMessage:
    """
    Base message model for all platforms.
    
    Can be extended by platform-specific implementations:
    - TelegramMessage
    - DiscordMessage
    """
    
    id: int
    """Message ID"""
    
    chat_id: int
    """Chat ID where message was sent"""
    
    from_user_id: Optional[int] = None
    """User ID who sent the message"""
    
    type: MessageType = MessageType.TEXT
    """Message type"""
    
    text: Optional[str] = None
    """Message text content"""
    
    caption: Optional[str] = None
    """Media caption"""
    
    date: datetime = field(default_factory=datetime.now)
    """When message was sent"""
    
    edit_date: Optional[datetime] = None
    """When message was last edited"""
    
    reply_to_message_id: Optional[int] = None
    """ID of message this replies to"""
    
    forward_from_chat_id: Optional[int] = None
    """Chat ID this message was forwarded from"""
    
    media_url: Optional[str] = None
    """URL to media file (if any)"""
    
    media_file_id: Optional[str] = None
    """File ID in platform storage"""
    
    raw_data: Optional[Any] = None
    """Raw platform-specific data"""
    
    @property
    def is_text(self) -> bool:
        """Check if this is a text message."""
        return self.type == MessageType.TEXT
    
    @property
    def is_media(self) -> bool:
        """Check if this is a media message."""
        return self.type in (
            MessageType.PHOTO,
            MessageType.VIDEO,
            MessageType.AUDIO,
            MessageType.DOCUMENT,
            MessageType.VOICE,
        )
    
    @property
    def is_reply(self) -> bool:
        """Check if this message is a reply."""
        return self.reply_to_message_id is not None
    
    @property
    def is_forward(self) -> bool:
        """Check if this message is forwarded."""
        return self.forward_from_chat_id is not None
    
    @property
    def is_edited(self) -> bool:
        """Check if this message was edited."""
        return self.edit_date is not None
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "chat_id": self.chat_id,
            "from_user_id": self.from_user_id,
            "type": self.type.value,
            "text": self.text,
            "caption": self.caption,
            "date": self.date.isoformat(),
            "edit_date": self.edit_date.isoformat() if self.edit_date else None,
            "reply_to_message_id": self.reply_to_message_id,
            "forward_from_chat_id": self.forward_from_chat_id,
            "media_url": self.media_url,
            "media_file_id": self.media_file_id,
        }
