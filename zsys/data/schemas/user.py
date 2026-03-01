"""User schemas for request/response validation."""

from datetime import datetime
from typing import Optional
from pydantic import Field, EmailStr
from .base import BaseSchema


class UserBase(BaseSchema):
    """Base user schema."""
    username: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: str = "en"


class UserCreate(UserBase):
    """User creation schema."""
    pass


class UserUpdate(BaseSchema):
    """User update schema."""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: Optional[str] = None


class UserResponse(UserBase):
    """User response schema."""
    id: int
    is_bot: bool = False
    is_premium: bool = False
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
