"""ZSYS core interfaces — Protocol-based structural abstractions.

All interfaces use ``typing.Protocol`` for structural subtyping, which
means implementations do not need to explicitly inherit from these classes.
Runtime ``isinstance()`` checks are supported via ``@runtime_checkable``.

Interfaces:
    IClient:     Base lifecycle + messaging contract for all platform clients.
    IBot:        Extended contract for regular bot clients.
    IChat:       Platform-agnostic chat/conversation representation.
    ChatType:    Enumeration of chat categories (private, group, channel, etc.).
    IStorage:    Generic key-value storage backend contract.
    ICipher:     Symmetric/asymmetric encryption/decryption contract.
    IBlockchain: Append-only chain contract (add, validate, balance, fetch).
    IWallet:     Crypto wallet contract (address, sign, send, query).
"""
# RU: Основные интерфейсы ZSYS — структурные абстракции на базе Protocol.
# RU: Реализации не обязаны явно наследовать — duck typing поддерживается.

from .blockchain import IBlockchain
from .bot import IBot, IUserBot
from .chat import ChatType, IChat
from .cipher import ICipher
from .client import IClient
from .storage import IStorage
from .wallet import IWallet

__all__ = [
    # Messaging
    "IClient",
    "IBot",
    "IUserBot",
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
