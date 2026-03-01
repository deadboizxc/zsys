"""
SQLAlchemy ORM models for database persistence.

All ORM models inherit from BaseModel which uses a single declarative_base.
This ensures all models share the same metadata for proper table creation.

For platform-agnostic data models without ORM, see zsys.core.models instead.

Structure:
    zsys/models/          → SQLAlchemy ORM models
    ├── base.py           → Base, BaseModel (DeclarativeBase)
    ├── user.py           → BaseUser (User) [ORM]
    ├── client.py         → BaseClient (Client) [ORM]
    ├── chat.py           → BaseChat (Chat) [ORM]
    ├── bot.py            → BaseBot (Bot) [ORM]
    ├── wallet.py         → BaseWallet (Wallet) [ORM]
    ├── message.py        → BaseMessage (Message) [ORM]
    └── media_file.py     → BaseMediaFile (MediaFile) [ORM]

Usage:
    from zsys.models import Base, BaseModel, User, Chat
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    # Setup database
    engine = create_engine("sqlite:///zsys.db")
    Base.metadata.create_all(engine)
    
    # Create user in database
    Session = sessionmaker(bind=engine)
    with Session() as session:
        user = User(id=123, username="john_doe", first_name="John")
        session.add(user)
        session.commit()
"""

# Base classes (single source of truth for ORM)
from .base import Base, BaseModel

# Domain models
from .user import BaseUser, User
from .client import BaseClient, Client
from .chat import BaseChat, Chat
from .bot import BaseBot, Bot
from .wallet import BaseWallet, Wallet
from .message import BaseMessage, Message
from .media_file import BaseMediaFile, MediaFile


__all__ = [
    # Core base classes
    'Base',
    'BaseModel',
    
    # Base models (preferred)
    'BaseUser',
    'BaseClient',
    'BaseChat',
    'BaseBot',
    'BaseWallet',
    'BaseMessage',
    'BaseMediaFile',
    
    # Backward compatible aliases
    'User',
    'Client',
    'Chat',
    'Bot',
    'Wallet',
    'Message',
    'MediaFile',
]
