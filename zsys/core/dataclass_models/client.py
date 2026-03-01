"""
BaseClient - Platform-agnostic client model.

Represents a bot or userbot client configuration.
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from enum import Enum


class ClientStatus(str, Enum):
    """Client status enumeration."""
    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class BaseClient:
    """
    Base client model.
    
    Represents configuration and state of a bot/userbot client.
    """
    
    name: str
    """Client name/identifier"""
    
    status: ClientStatus = ClientStatus.IDLE
    """Current client status"""
    
    api_id: Optional[int] = None
    """API ID (for Telegram, etc.)"""
    
    api_hash: Optional[str] = None
    """API hash"""
    
    token: Optional[str] = None
    """Bot token (for bot clients)"""
    
    session_name: Optional[str] = None
    """Session name (for userbots)"""
    
    phone_number: Optional[str] = None
    """Phone number (for userbots)"""
    
    started_at: Optional[datetime] = None
    """When client was started"""
    
    stopped_at: Optional[datetime] = None
    """When client was stopped"""
    
    error_message: Optional[str] = None
    """Last error message (if status is ERROR)"""
    
    created_at: datetime = field(default_factory=datetime.now)
    """When this client was created"""
    
    @property
    def is_running(self) -> bool:
        """Check if client is currently running."""
        return self.status == ClientStatus.RUNNING
    
    @property
    def is_bot(self) -> bool:
        """Check if this is a bot client (has token)."""
        return self.token is not None
    
    @property
    def is_userbot(self) -> bool:
        """Check if this is a userbot client (has phone/session)."""
        return self.phone_number is not None or self.session_name is not None
    
    @property
    def uptime(self) -> Optional[int]:
        """
        Get uptime in seconds.
        
        Returns:
            Uptime in seconds or None if not running
        """
        if self.started_at and self.status == ClientStatus.RUNNING:
            return int((datetime.now() - self.started_at).total_seconds())
        return None
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "status": self.status.value,
            "is_bot": self.is_bot,
            "is_userbot": self.is_userbot,
            "is_running": self.is_running,
            "uptime": self.uptime,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "stopped_at": self.stopped_at.isoformat() if self.stopped_at else None,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat(),
        }
