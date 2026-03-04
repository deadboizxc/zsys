"""Wallet schemas for request/response validation."""

from datetime import datetime
from typing import Optional

from pydantic import Field

from .base import BaseSchema


class WalletBase(BaseSchema):
    """Base wallet schema."""

    address: str = Field(..., min_length=26, max_length=255)
    label: Optional[str] = None


class WalletCreate(WalletBase):
    """Wallet creation schema."""

    pass


class WalletResponse(WalletBase):
    """Wallet response schema."""

    id: int
    balance: str
    user_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
