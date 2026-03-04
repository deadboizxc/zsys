"""
Unified Pydantic schemas for API requests/responses.

All schemas inherit from BaseSchema for consistent configuration.

Structure:
    zsys/schemas/
    ├── base.py     → BaseSchema, TimestampMixin, IdMixin, PagedResponse
    ├── user.py     → UserBase, UserCreate, UserUpdate, UserResponse
    ├── client.py   → ClientBase, ClientCreate, ClientUpdate, ClientResponse
    ├── chat.py     → ChatBase, ChatCreate, ChatResponse
    ├── bot.py      → BotBase, BotCreate, BotUpdate, BotResponse
    ├── message.py  → MessageBase, MessageCreate, MessageResponse
    ├── wallet.py   → WalletBase, WalletCreate, WalletResponse
    ├── media.py    → MediaBase, MediaCreate, MediaUpdate, MediaResponse, ...
    └── common.py   → ErrorResponse, TokenRequest, TokenResponse, ListResponse

Usage:
    from zsys.data.schemas import BaseSchema, UserCreate, UserResponse
"""

# Base schema class (single source of truth)
from .base import (
    ApiResponse,
    BaseEntitySchema,
    BaseSchema,
    IdMixin,
    PagedResponse,
    TimestampMixin,
)

# Bot schemas
from .bot import BotBase, BotCreate, BotResponse, BotResponseWithToken, BotUpdate

# Chat schemas
from .chat import ChatBase, ChatCreate, ChatResponse

# Client schemas
from .client import ClientBase, ClientCreate, ClientResponse, ClientUpdate

# Common schemas
from .common import ErrorResponse, ListResponse, TokenRequest, TokenResponse

# Media schemas
from .media import (
    MediaBase,
    MediaCreate,
    MediaListResponse,
    MediaResponse,
    MediaUpdate,
    PaginationMeta,
)

# Message schemas
from .message import MessageBase, MessageCreate, MessageResponse

# User schemas
from .user import UserBase, UserCreate, UserResponse, UserUpdate

# Wallet schemas
from .wallet import WalletBase, WalletCreate, WalletResponse

__all__ = [
    # Base
    "BaseSchema",
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    # Client
    "ClientBase",
    "ClientCreate",
    "ClientUpdate",
    "ClientResponse",
    # Chat
    "ChatBase",
    "ChatCreate",
    "ChatResponse",
    # Bot
    "BotBase",
    "BotCreate",
    "BotUpdate",
    "BotResponse",
    "BotResponseWithToken",
    # Message
    "MessageBase",
    "MessageCreate",
    "MessageResponse",
    # Wallet
    "WalletBase",
    "WalletCreate",
    "WalletResponse",
    # Media
    "MediaBase",
    "MediaCreate",
    "MediaUpdate",
    "MediaResponse",
    "PaginationMeta",
    "MediaListResponse",
    # Common
    "ErrorResponse",
    "TokenRequest",
    "TokenResponse",
    "ListResponse",
]
