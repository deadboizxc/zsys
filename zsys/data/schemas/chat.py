"""Chat schemas for request/response validation."""

from datetime import datetime
from typing import Optional
from pydantic import Field
from .base import BaseSchema


class ChatBase(BaseSchema):
    """Base chat schema."""
    title: str = Field(..., min_length=1, max_length=255)
    type: str = Field(..., description="private, group, supergroup, channel")


class ChatCreate(ChatBase):
    """Chat creation schema."""
    members_count: int = 0


class ChatResponse(ChatBase):
    """Chat response schema."""
    id: int
    username: Optional[str] = None
    members_count: int
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
