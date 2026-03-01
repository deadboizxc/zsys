"""Common/utility schemas."""

from typing import Optional, Any, Dict
from pydantic import Field
from .base import BaseSchema


class ErrorResponse(BaseSchema):
    """Error response schema."""
    error: str
    code: str
    detail: Optional[str] = None


class TokenRequest(BaseSchema):
    """Token generation request."""
    user_id: str


class TokenResponse(BaseSchema):
    """Token response."""
    token: str
    token_type: str = "bearer"
    expires_in: int


class ListResponse(BaseSchema):
    """Generic list response."""
    items: list
    total: int
    skip: int
    limit: int
