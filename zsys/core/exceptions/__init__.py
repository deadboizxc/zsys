"""
ZSYS Exception classes.

All ZSYS exceptions inherit from BaseException base class.

Exception Hierarchy:
    BaseException (base)
    ├── ConfigError (configuration)
    ├── DatabaseError (database operations)
    ├── StorageError (storage operations)
    ├── ClientError (client operations)
    ├── AuthenticationError (auth/authorization)
    ├── SessionError (session management)
    ├── ValidationError (data validation)
    ├── NetworkError (network/connection)
    ├── TimeoutError (timeout errors)
    ├── NotFoundError (resource not found)
    ├── PermissionError (access denied)
    ├── PermissionDeniedError (permission denied with action)
    ├── CryptoError (cryptography)
    ├── BlockchainError (blockchain)
    │   └── TransactionError (transactions)
    ├── MediaError (media operations)
    │   ├── MediaNotFoundError (media not found)
    │   ├── MediaExistsError (media exists)
    │   └── InvalidMediaTypeError (invalid media type)
    ├── ModuleError (module loading)
    ├── FileError (file operations)
    ├── APIError (API/HTTP)
    ├── BotError (bot operations)
    └── LicenseError (licensing)
"""

from .base import BaseException, BaseException
from .config import ConfigError
from .storage import DatabaseError, StorageError
from .client import ClientError, AuthenticationError, SessionError
from .validation import ValidationError
from .network import NetworkError, TimeoutError
from .resource import NotFoundError, PermissionError, PermissionDeniedError
from .crypto import CryptoError
from .blockchain import BlockchainError, TransactionError
from .media import MediaError, MediaNotFoundError, MediaExistsError, InvalidMediaTypeError
from .module import ModuleError, FileError
from .api import APIError, BotError
from .license import LicenseError

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

from .blockchain import BlockchainError, TransactionError


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
