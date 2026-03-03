"""Bot schemas for request/response validation."""

from datetime import datetime
from typing import Optional

from pydantic import Field

from .base import BaseSchema


class BotBase(BaseSchema):
    """Base bot schema with common fields."""

    name: str = Field(..., min_length=1, max_length=100)
    bot_type: str = Field(
        ..., description="Platform: telegram, instagram, discord, etc."
    )
    description: Optional[str] = None


class BotCreate(BotBase):
    """Bot creation schema."""

    owner_id: int = Field(..., description="ID of the user who owns this bot")
    token: str = Field(..., min_length=10, description="Bot API token")


class BotUpdate(BaseSchema):
    """Bot update schema."""

    name: Optional[str] = None
    description: Optional[str] = None
    token: Optional[str] = None
    is_active: Optional[bool] = None
    is_running: Optional[bool] = None


class BotResponse(BotBase):
    """Bot response schema."""

    id: int
    owner_id: int
    is_active: bool = True
    is_running: bool = False
    created_at: datetime
    updated_at: datetime
    # Note: token is intentionally excluded from response for security


class BotResponseWithToken(BotResponse):
    """Bot response schema including token (for owner only)."""

    token: str


__all__ = ["BotBase", "BotCreate", "BotUpdate", "BotResponse", "BotResponseWithToken"]
