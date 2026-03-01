"""
Core Interfaces - Protocol-based abstractions.

All interfaces use typing.Protocol for structural subtyping.
This allows implementations without explicit inheritance.

Interfaces:
    - IClient: Base client interface for messaging platforms
    - IBot: Bot client interface (regular bots)
    - IChat: Chat interface (private, group, channel)
    - IStorage: Generic key-value storage interface
    - ICipher: Encryption/decryption interface
    - IBlockchain: Blockchain interface
    - IWallet: Crypto wallet interface
"""

from .client import IClient
from .bot import IBot
from .chat import IChat, ChatType
from .storage import IStorage
from .cipher import ICipher
from .blockchain import IBlockchain
from .wallet import IWallet


__all__ = [
    # Messaging
    "IClient",
    "IBot",
    "IChat",
    "ChatType",
    # Storage
    "IStorage",
    # Crypto
    "ICipher",
    # Blockchain
    "IBlockchain",
    "IWallet",
]
