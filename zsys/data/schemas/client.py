"""Client schemas for request/response validation."""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import Field

from .base import BaseSchema


class ClientBase(BaseSchema):
    """Base client schema with common fields."""

    client_type: str = Field(
        ..., description="Platform: telegram, instagram, discord, etc."
    )
    client_id: str = Field(..., description="User ID in the external service")
    username: Optional[str] = None


class ClientCreate(ClientBase):
    """Client creation schema."""

    user_id: int = Field(..., description="ID of the user who owns this client")
    extra_data: Optional[Dict[str, Any]] = None


class ClientUpdate(BaseSchema):
    """Client update schema."""

    username: Optional[str] = None
    is_connected: Optional[bool] = None
    extra_data: Optional[Dict[str, Any]] = None


class ClientResponse(ClientBase):
    """Client response schema."""

    id: int
    user_id: int
    is_connected: bool = True
    extra_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


__all__ = ["ClientBase", "ClientCreate", "ClientUpdate", "ClientResponse"]
