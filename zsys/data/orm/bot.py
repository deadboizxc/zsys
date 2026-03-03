"""BaseBot model - bot instance entity."""

from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, Text

from .base import BaseModel


class BaseBot(BaseModel):
    """
    Base Bot model - represents a bot instance.

    Supports multiple bot types: Telegram, Instagram, Discord, etc.

    Attributes:
        name: Bot name/identifier
        bot_type: Platform ('telegram', 'instagram', 'discord', etc.)
        owner_id: Foreign key to the User who owns this bot
        token: Bot API token (store securely!)
        description: Bot description
        is_active: Whether the bot is enabled
        is_running: Whether the bot is currently running
    """

    __tablename__ = "bots"

    name = Column(String(100), nullable=False, unique=True)
    bot_type = Column(String(50), nullable=False, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    is_running = Column(Boolean, default=False)

    def __repr__(self) -> str:
        return f"<BaseBot(id={self.id}, name={self.name}, type={self.bot_type})>"


# Backward compatible alias
Bot = BaseBot

__all__ = ["BaseBot", "Bot"]
