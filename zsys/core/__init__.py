"""ZSYS core — pure abstraction layer.

This package contains ONLY abstract interfaces, base data models,
configuration classes, logging utilities, and the exception hierarchy.
No concrete implementations or external library dependencies are allowed here.

Architecture::

    zsys/core/
    ├── interfaces/   — Protocol-based structural interfaces
    ├── dataclass_models/ — Platform-agnostic data models (dataclasses)
    ├── config/       — Pydantic-based configuration management
    ├── logging/      — Logging utilities
    └── exceptions/   — Full exception class hierarchy
"""
# RU: Основной пакет ZSYS — чистый слой абстракций.
# RU: Только интерфейсы, модели, конфигурация, логирование и исключения.

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

from .config import BaseConfig
from .dataclass_models import (
    BaseBot,
    BaseChat,
    BaseClient,
    BaseMessage,
    BaseUser,
    BaseWallet,
)
from .exceptions import (
    AuthenticationError,
    BaseException,
    BlockchainError,
    ClientError,
    ConfigError,
    CryptoError,
    DatabaseError,
    NetworkError,
    NotFoundError,
    PermissionError,
    StorageError,
    TimeoutError,
    TransactionError,
    ValidationError,
)
from .logging import ILogger

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
    "ILogger",
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
