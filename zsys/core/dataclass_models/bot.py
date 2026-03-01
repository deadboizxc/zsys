"""BaseBot model - bot instance entity (dataclass)."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class BaseBot:
    """
    Platform-agnostic bot data model.
    
    Represents a bot instance without ORM dependencies.
    For database persistence, use zsys.models.BaseBot instead.
    
    Attributes:
        id: Unique bot identifier
        name: Bot name/identifier
        bot_type: Platform ('telegram', 'instagram', 'discord', etc.)
        owner_id: ID of the user who owns this bot
        token: Bot API token
        description: Bot description
        is_active: Whether the bot is enabled
        is_running: Whether the bot is currently running
    """
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
