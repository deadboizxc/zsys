"""Message schemas for request/response validation."""

from datetime import datetime
from typing import Optional
from pydantic import Field
from .base import BaseSchema


class MessageBase(BaseSchema):
    """Base message schema."""
    text: str = Field(..., min_length=1, max_length=4096)
    chat_id: int


class MessageCreate(MessageBase):
    """Message creation schema."""
    pass


class MessageResponse(MessageBase):
    """Message response schema."""
    id: int
    user_id: Optional[int] = None
    is_bot_message: bool = False
    created_at: datetime
    updated_at: datetime
