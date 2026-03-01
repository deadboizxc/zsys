"""
BaseUser - Platform-agnostic user model.

Represents a user in any messaging platform or system.
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class BaseUser:
    """
    Base user model for all platforms.
    
    Can be extended by platform-specific implementations:
    - TelegramUser
    - DiscordUser
    - WebUser
    """
    
    id: int
    """Unique user ID"""
    
    username: Optional[str] = None
    """Username (without @)"""
    
    first_name: Optional[str] = None
    """User's first name"""
    
    last_name: Optional[str] = None
    """User's last name"""
    
    is_bot: bool = False
    """Whether this user is a bot"""
    
    is_premium: bool = False
    """Whether this user has premium status"""
    
    language_code: Optional[str] = None
    """User's language code (e.g., 'en', 'ru')"""
    
    phone_number: Optional[str] = None
    """User's phone number (if available)"""
    
    created_at: datetime = field(default_factory=datetime.now)
    """When this user record was created"""
    
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return "Unknown User"
    
    @property
    def mention(self) -> str:
        """Get user mention (username or full name)."""
        if self.username:
            return f"@{self.username}"
        return self.full_name
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "is_bot": self.is_bot,
            "is_premium": self.is_premium,
            "language_code": self.language_code,
            "phone_number": self.phone_number,
            "created_at": self.created_at.isoformat(),
        }
