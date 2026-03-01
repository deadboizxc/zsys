"""Media schemas for request/response validation."""

from datetime import datetime
from typing import List, Optional
from pydantic import Field
from .base import BaseSchema


class MediaBase(BaseSchema):
    """Base media schema."""
    filename: str
    mime_type: str
    size: int = Field(..., gt=0)
    media_type: str = "file"


class MediaCreate(MediaBase):
    """Media creation schema."""
    url: str
    storage_path: Optional[str] = None


class MediaUpdate(BaseSchema):
    """Media update schema."""
    filename: Optional[str] = None
    media_type: Optional[str] = None


class MediaResponse(MediaBase):
    """Media response schema."""
    id: int
    url: str
    storage_path: Optional[str] = None
    file_hash: Optional[str] = None
    owner_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class PaginationMeta(BaseSchema):
    """Pagination metadata."""
    total: int
    limit: int
    offset: int
    has_more: bool


class MediaListResponse(BaseSchema):
    """Response for media list."""
    items: List[MediaResponse]
    meta: PaginationMeta
