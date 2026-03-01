"""
ZSYS - Modular Python Ecosystem

A flexible framework for building bots, userbots, APIs, storage solutions,
blockchain integrations, and crypto services.

Modules:
- core: Base interfaces and models (Protocol-based)
- models: ORM models (SQLAlchemy-based)
- plugins: Dynamic plugin system with command routing
- telegram: Telegram bot/userbot implementations (Pyrogram, Aiogram, Telethon)
- storage: Storage backends (SQLite, Redis, Memory, etc.)
- crypto: Encryption implementations (AES, RSA, ECC)
- blockchain: Blockchain integrations (Simple Chain, EVM Chain)
- api: API adapters (FastAPI)
- modules: Dynamic module loading system
- schemas: Pydantic schemas for data validation
- security: Security and licensing utilities
- transport: HTTP and WebSocket clients
- utils: Utility functions
- resources: Static resources (fonts, images, locales, templates)

Usage:
    # Core interfaces (Protocol-based)
    from zsys.core.interfaces import IClient, IBot, IStorage
    from zsys.core.models import BaseUser, BaseChat
    
    # ORM models (SQLAlchemy)
    from zsys.models import Base, BaseModel, User, Chat
    
    # Plugin system
    from zsys.plugins import CommandRouter, command, Context
    
    # Implementations
    from zsys.telegram.pyrogram import PyrogramClient
    from zsys.storage.sqlite import SQLiteStorage
"""

__version__ = "1.0.0"
__author__ = "deadboizxc"

# Core exports
# TODO: Restore when interfaces module exists
# from zsys.core.interfaces import (
#     IClient,
#     IBot,
#     IChat,
#     ChatType,
#     IStorage,
#     ICipher,
#     IBlockchain,
#     IWallet,
# )

__all__ = [
    "__version__",
    "__author__",
    # Interfaces (commented until interfaces module exists)
    # "IClient",
    # "IBot",
    # "IChat",
    # "ChatType",
    # "IStorage",
    # "ICipher",
    # "IBlockchain",
    # "IWallet",
]
