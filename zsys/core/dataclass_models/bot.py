"""BaseBot dataclass — platform-agnostic bot instance model.

Provides a pure-Python data structure representing a bot without any
ORM or external dependencies.  For database persistence use
``zsys.data.orm.bot.BaseBot`` instead.
"""
# RU: Датакласс BaseBot — платформо-независимая модель экземпляра бота.
# RU: Для сохранения в БД используйте zsys.data.orm.bot.BaseBot.

from dataclasses import dataclass
from typing import Optional


@dataclass
class BaseBot:
    """Platform-agnostic bot data model.

    Represents a bot instance in memory without ORM or database dependencies.
    Use this class for in-process data transfer, API contracts, and testing.
    For database persistence, use ``zsys.data.orm.bot.BaseBot`` instead.

    Attributes:
        id: Unique numeric bot identifier.
        name: Bot name or display identifier.
        bot_type: Messaging platform (``"telegram"``, ``"discord"``, etc.).
        owner_id: Numeric ID of the user who owns this bot.
        token: Bot API token — store and handle securely.
        description: Optional human-readable description of the bot.
        is_active: Whether the bot is enabled and allowed to operate.
        is_running: Whether the bot is currently connected and polling.
    """
    # RU: Платформо-независимая модель данных бота в памяти.

    id: int
    name: str
    bot_type: str
    owner_id: int
    token: str
    description: Optional[str] = None
    is_active: bool = True
    is_running: bool = False


# Backward compatible alias
Bot = BaseBot

__all__ = ['BaseBot', 'Bot']
