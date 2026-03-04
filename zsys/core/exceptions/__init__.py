"""ZSYS exceptions — full hierarchy of typed errors.

All exceptions inherit from BaseException which provides optional
machine-readable error codes and structured details dictionaries.

Exception Hierarchy::

    BaseException (base)
    ├── ConfigError           — configuration loading/validation
    ├── DatabaseError         — database operations
    ├── StorageError          — key-value storage operations
    ├── ClientError           — bot/userbot client operations
    ├── AuthenticationError   — auth/authorisation failures
    ├── SessionError          — session management
    ├── ValidationError       — data validation (code="VALIDATION_ERROR")
    ├── NetworkError          — network/connection errors
    ├── TimeoutError          — timeout errors
    ├── NotFoundError         — resource not found
    ├── PermissionError       — access denied
    ├── PermissionDeniedError — permission denied with action context
    ├── CryptoError           — cryptographic operations
    ├── BlockchainError       — blockchain operations
    │   └── TransactionError  — transaction-level failures
    ├── MediaError            — media operations
    │   ├── MediaNotFoundError    — media file not found
    │   ├── MediaExistsError      — duplicate media (hash collision)
    │   └── InvalidMediaTypeError — unsupported MIME type
    ├── ModuleError           — plugin module loading
    ├── FileError             — filesystem operations
    ├── APIError              — external API / HTTP errors
    ├── BotError              — bot-platform-level errors
    └── LicenseError          — license validation/activation
"""
# RU: Иерархия исключений ZSYS — типизированные ошибки всех уровней.
# RU: Все наследуют BaseException с опциональными кодами и словарём деталей.

from .api import APIError, BotError
from .base import BaseException
from .blockchain import BlockchainError, TransactionError
from .client import AuthenticationError, ClientError, SessionError
from .config import ConfigError
from .crypto import CryptoError
from .license import LicenseError
from .media import (
    InvalidMediaTypeError,
    MediaError,
    MediaExistsError,
    MediaNotFoundError,
)
from .module import FileError, ModuleError
from .network import NetworkError, TimeoutError
from .resource import NotFoundError, PermissionDeniedError, PermissionError
from .storage import DatabaseError, StorageError
from .validation import ValidationError

__all__ = [
    # Base
    "BaseException",
    # Configuration
    "ConfigError",
    # Storage
    "DatabaseError",
    "StorageError",
    # Client
    "ClientError",
    "AuthenticationError",
    "SessionError",
    # Validation
    "ValidationError",
    # Network
    "NetworkError",
    "TimeoutError",
    # Resource
    "NotFoundError",
    "PermissionError",
    "PermissionDeniedError",
    # Crypto
    "CryptoError",
    # Blockchain
    "BlockchainError",
    "TransactionError",
    # Media
    "MediaError",
    "MediaNotFoundError",
    "MediaExistsError",
    "InvalidMediaTypeError",
    # Module
    "ModuleError",
    "FileError",
    # API
    "APIError",
    "BotError",
    # License
    "LicenseError",
]


__all__ = [
    # Base
    "BaseException",
    # Config
    "ConfigError",
    # Storage
    "DatabaseError",
    "StorageError",
    # Client
    "ClientError",
    "AuthenticationError",
    # Validation
    "ValidationError",
    # Network
    "NetworkError",
    "TimeoutError",
    # Resource
    "NotFoundError",
    "PermissionError",
    # Crypto
    "CryptoError",
    # Blockchain
    "BlockchainError",
    "TransactionError",
]
