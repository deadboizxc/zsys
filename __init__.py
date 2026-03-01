"""
ZSYS - Modular Python Ecosystem

A modular Python ecosystem for bots, userbots, APIs, storage, blockchain, and crypto services.
"""

__version__ = "3.0.0"
__author__ = "deadboizxc"
__email__ = "deadboi.zxc@gmail.com"
__license__ = "MIT"

# Core exports
from core import (
    # Interfaces
    IBot,
    IClient,
    IChat,
    IStorage,
    ICipher,
    IBlockchain,
    IWallet,
    # Models
    BaseUser,
    BaseChat,
    BaseClient,
    BaseMessage,
    BaseWallet,
    BaseTransaction,
    # Config & Utilities
    BaseConfig,
    Logger,
    BaseException,
)

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__email__",
    "__license__",
    # Core interfaces
    "IBot",
    "IClient",
    "IUserBot",
    "IChat",
    "IStorage",
    "ICipher",
    "IBlockchain",
    "IWallet",
    # Core models
    "BaseUser",
    "BaseChat",
    "BaseClient",
    "BaseMessage",
    "BaseWallet",
    "BaseTransaction",
    # Config & Utils
    "BaseConfig",
    "Logger",
    "BaseException",
]
