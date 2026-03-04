"""BaseChat model - conversation/channel entity."""

from sqlalchemy import Boolean, Column, Integer, String

from .base import BaseModel


class BaseChat(BaseModel):
    """
    Base Chat model - represents a conversation or channel.

    Supports all chat types: private, group, supergroup, channel.

    Attributes:
        title: Chat title or display name
        username: Public chat username (if any)
        type: Chat type ('private', 'group', 'supergroup', 'channel')
        members_count: Number of participants
        is_active: Whether the chat is active
    """

    __tablename__ = "chats"

    title = Column(String(255), nullable=False)
    username = Column(String(100), nullable=True, index=True)
    type = Column(String(20), nullable=False)  # private, group, supergroup, channel
    members_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True, index=True)

    @property
    def is_private(self) -> bool:
        return self.type == "private"

    @property
    def is_group(self) -> bool:
        return self.type in ("group", "supergroup")

    @property
    def is_channel(self) -> bool:
        return self.type == "channel"

    def __repr__(self) -> str:
        return f"<BaseChat(id={self.id}, title={self.title}, type={self.type})>"


# Backward compatible alias
Chat = BaseChat

__all__ = ["BaseChat", "Chat"]
