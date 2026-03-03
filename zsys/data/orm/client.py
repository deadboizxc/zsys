"""BaseClient model - messaging service client entity."""

from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, JSON

from .base import BaseModel


class BaseClient(BaseModel):
    """
    Base Client model - represents a connection to an external messaging service.

    A single User can have multiple Clients (e.g., Telegram, Instagram, Discord).

    Attributes:
        user_id: Foreign key to the User who owns this client
        client_type: Platform identifier ('telegram', 'instagram', 'discord', etc.)
        client_id: User's ID in the external service
        username: User's username in the external service
        is_connected: Whether the client session is active
        extra_data: Platform-specific additional data (JSON)
    """

    __tablename__ = "clients"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    client_type = Column(String(50), nullable=False, index=True)
    client_id = Column(String(255), nullable=False, unique=True, index=True)
    username = Column(String(255), nullable=True)
    is_connected = Column(Boolean, default=True, index=True)
    extra_data = Column(JSON, nullable=True)

    def __repr__(self) -> str:
        return f"<BaseClient(user_id={self.user_id}, type={self.client_type}, id={self.client_id})>"


# Backward compatible alias
Client = BaseClient

__all__ = ["BaseClient", "Client"]
