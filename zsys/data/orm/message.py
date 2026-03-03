"""BaseMessage model - chat message entity."""

from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Text

from .base import BaseModel


class BaseMessage(BaseModel):
    """
    Base Message model - represents a chat message.

    Attributes:
        text: Message text content
        chat_id: ID of the chat where message was sent
        user_id: ID of the user who sent the message (nullable for system messages)
        is_bot_message: Whether the message was sent by a bot
        reply_to_message_id: ID of the message this is a reply to (optional)
    """

    __tablename__ = "messages"

    text = Column(Text, nullable=False)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    is_bot_message = Column(Boolean, default=False)
    reply_to_message_id = Column(Integer, nullable=True)

    def __repr__(self) -> str:
        preview = self.text[:30] + "..." if len(self.text) > 30 else self.text
        return f"<BaseMessage(id={self.id}, chat_id={self.chat_id}, text='{preview}')>"


# Backward compatible alias
Message = BaseMessage

__all__ = ["BaseMessage", "Message"]
