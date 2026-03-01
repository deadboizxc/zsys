"""
ZSYS Core - Pure abstraction layer.

This package contains ONLY abstract interfaces, base models, and helpers.
NO concrete implementations or external library dependencies allowed.

Architecture:
- interfaces/: Protocol-based interfaces (IBot, IClient, IStorage, etc.)
- models/: Base data models (BaseUser, BaseChat, BaseClient, etc.)
- config/: Configuration management
- logging/: Logging utilities
- exceptions/: Exception classes hierarchy
"""

# TODO: Restore when interfaces module exists
# from .interfaces import (
#     IBot,
#     IClient,
#     IChat,
#     ChatType,
#     IStorage,
#     ICipher,
#     IBlockchain,
#     IWallet,
# )

from .dataclass_models import (
    BaseUser,
    BaseChat,
    BaseClient,
    BaseMessage,
    BaseWallet,
    BaseBot,
)

from .config import BaseConfig
from .logging import Logger
from .exceptions import (
    BaseException,
    ConfigError,
    DatabaseError,
    StorageError,
    ClientError,
    AuthenticationError,
    ValidationError,
    NetworkError,
    TimeoutError,
    NotFoundError,
    PermissionError,
    CryptoError,
    BlockchainError,
    TransactionError,
)

__version__ = "3.0.0"

__all__ = [
    # Interfaces (commented until interfaces module exists)
    # "IBot",
    # "IClient",
    # "IChat",
    # "ChatType",
    # "IStorage",
    # "ICipher",
    # "IBlockchain",
    # "IWallet",
    # Models
    "BaseUser",
    "BaseChat",
    "BaseClient",
    "BaseMessage",
    "BaseWallet",
    "BaseBot",
    # Config & Utilities
    "BaseConfig",
    "Logger",
    # Exceptions
    "BaseException",
    "ConfigError",
    "DatabaseError",
    "StorageError",
    "ClientError",
    "AuthenticationError",
    "ValidationError",
    "NetworkError",
    "TimeoutError",
    "NotFoundError",
    "PermissionError",
    "CryptoError",
    "BlockchainError",
    "TransactionError",
]
