"""
Platform-agnostic data models for ZSYS.

These models are simple data structures (dataclasses/Pydantic) without ORM dependencies.
Use these for in-memory data representation and API contracts.

For database persistence with SQLAlchemy ORM, see zsys.models instead.

Structure:
    zsys/core/models/     → Platform-agnostic data models
    ├── user.py           → BaseUser (dataclass)
    ├── chat.py           → BaseChat (dataclass)
    ├── client.py         → BaseClient (dataclass)
    ├── message.py        → BaseMessage (dataclass)
    ├── wallet.py         → BaseWallet (dataclass)
    └── bot.py            → BaseBot (dataclass)

Usage:
    from zsys.core.models import BaseUser, BaseChat, BaseMessage
    
    # Create in-memory user object
    user = BaseUser(id=123, username="john_doe", first_name="John")
"""

from .user import BaseUser
from .chat import BaseChat
from .client import BaseClient
from .message import BaseMessage
from .wallet import BaseWallet
from .bot import BaseBot

__all__ = [
    "BaseUser",
    "BaseChat",
    "BaseClient",
    "BaseMessage",
    "BaseWallet",
    "BaseBot",
]

from .context import Context, User, Chat

__all__ += ["Context", "User", "Chat"]
