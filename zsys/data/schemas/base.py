"""
Base Pydantic schemas for API responses/requests.

This is the CANONICAL source for BaseSchema.
All Pydantic schemas should inherit from BaseSchema.

Example:
    from zsys.data.schemas.base import BaseSchema

    class UserSchema(BaseSchema):
        id: int
        username: str
        email: str
"""

from datetime import datetime
from typing import Any, Dict, Optional, List, TypeVar, Generic

from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    """
    Base Pydantic schema with ORM support.

    All API schemas should inherit from this class.

    Features:
    - from_attributes=True (ORM mode)
    - Camel case alias generation (optional)
    - JSON serialization support
    """

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
        arbitrary_types_allowed=True,
        str_strip_whitespace=True,
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump()

    def to_json(self) -> str:
        """Convert to JSON string."""
        return self.model_dump_json()


class TimestampMixin(BaseSchema):
    """Mixin for models with timestamps."""

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class IdMixin(BaseSchema):
    """Mixin for models with ID."""

    id: int


class BaseEntitySchema(IdMixin, TimestampMixin):
    """Base schema for database entities with id and timestamps."""

    pass


# Generic response types
T = TypeVar("T")


class PagedResponse(BaseSchema, Generic[T]):
    """Generic paginated response."""

    items: List[T]
    total: int
    page: int = Field(ge=1, default=1)
    page_size: int = Field(ge=1, le=100, default=20)

    @property
    def total_pages(self) -> int:
        return (self.total + self.page_size - 1) // self.page_size

    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages

    @property
    def has_prev(self) -> bool:
        return self.page > 1


class ApiResponse(BaseSchema, Generic[T]):
    """Standard API response wrapper."""

    success: bool = True
    data: Optional[T] = None
    error: Optional[str] = None
    message: Optional[str] = None


__all__ = [
    "BaseSchema",
    "TimestampMixin",
    "IdMixin",
    "BaseEntitySchema",
    "PagedResponse",
    "ApiResponse",
]
