"""ZSYS platform-agnostic data models — in-memory DTOs and context types.

These are pure Python dataclasses without ORM or external library dependencies.
Use them for in-memory data representation, API contracts, and testing.

For database persistence with SQLAlchemy ORM, use ``zsys.data.orm`` instead.

Structure::

    zsys/core/dataclass_models/
    ├── user.py      → BaseUser    (dataclass)
    ├── chat.py      → BaseChat    (dataclass)
    ├── client.py    → BaseClient  (dataclass)
    ├── message.py   → BaseMessage (dataclass)
    ├── wallet.py    → BaseWallet  (dataclass)
    ├── bot.py       → BaseBot     (dataclass)
    └── context.py   → Context (ABC), User, Chat (dataclasses)

Example::

    from zsys.core.dataclass_models import BaseUser, BaseChat, BaseMessage

    user = BaseUser(id=123, username="john_doe", first_name="John")
"""
# RU: Платформо-независимые датаклассы ZSYS — DTO и типы контекста.
# RU: Без зависимостей от ORM; для БД используйте zsys.data.orm.

from .user import BaseUser
from .chat import BaseChat
from .client import BaseClient
from .message import BaseMessage
from .wallet import BaseWallet, BaseTransaction, TransactionStatus
from .bot import BaseBot

__all__ = [
    "BaseUser",
    "BaseChat",
    "BaseClient",
    "BaseMessage",
    "BaseWallet",
    "BaseTransaction",
    "TransactionStatus",
    "BaseBot",
]

from .context import Context, User, Chat

__all__ += ["Context", "User", "Chat"]
