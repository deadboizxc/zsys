"""BaseMessage dataclass — platform-agnostic message model.

Represents a message in any messaging platform without ORM or
platform-specific dependencies.
"""
# RU: Датакласс BaseMessage — платформо-независимая модель сообщения.
# RU: Для сохранения в БД используйте zsys.data.orm.message.BaseMessage.

from dataclasses import dataclass, field
from typing import Optional, Any
from datetime import datetime
from enum import Enum


class MessageType(str, Enum):
    """Enumeration of supported message content types.

    Values are lowercase strings that match common platform API responses.
    """

    # RU: Перечисление поддерживаемых типов содержимого сообщений.
    TEXT = "text"
    PHOTO = "photo"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    VOICE = "voice"
    STICKER = "sticker"
    ANIMATION = "animation"
    LOCATION = "location"
    CONTACT = "contact"
    POLL = "poll"
    SERVICE = "service"


@dataclass
class BaseMessage:
    """Platform-agnostic base message model.

    Represents a single message from any platform.  Can be extended by
    platform-specific subclasses (TelegramMessage, DiscordMessage).

    Attributes:
        id: Platform-unique numeric message identifier.
        chat_id: Numeric ID of the chat where the message was sent.
        from_user_id: Numeric ID of the sender; None for anonymous/channel posts.
        type: Content type of the message.
        text: Text content; None for non-text message types.
        caption: Media caption text; None if no caption.
        date: Timestamp when the message was originally sent.
        edit_date: Timestamp of the last edit; None if never edited.
        reply_to_message_id: ID of the message being replied to; None otherwise.
        forward_from_chat_id: Original chat ID for forwarded messages; None otherwise.
        media_url: URL to the attached media file; None if no media.
        media_file_id: Platform storage file ID; None if no media.
        raw_data: Raw platform-specific message object for advanced use.
    """

    # RU: Платформо-независимая модель сообщения в памяти.

    id: int
    """Message ID"""

    chat_id: int
    """Chat ID where message was sent"""

    from_user_id: Optional[int] = None
    """User ID who sent the message"""

    type: MessageType = MessageType.TEXT
    """Message type"""

    text: Optional[str] = None
    """Message text content"""

    caption: Optional[str] = None
    """Media caption"""

    date: datetime = field(default_factory=datetime.now)
    """When message was sent"""

    edit_date: Optional[datetime] = None
    """When message was last edited"""

    reply_to_message_id: Optional[int] = None
    """ID of message this replies to"""

    forward_from_chat_id: Optional[int] = None
    """Chat ID this message was forwarded from"""

    media_url: Optional[str] = None
    """URL to media file (if any)"""

    media_file_id: Optional[str] = None
    """File ID in platform storage"""

    raw_data: Optional[Any] = None
    """Raw platform-specific data"""

    @property
    def is_text(self) -> bool:
        """True if this message contains plain text with no media.

        Returns:
            True when type is ``MessageType.TEXT``.
        """
        # RU: True, если сообщение является текстовым (без медиа).
        return self.type == MessageType.TEXT

    @property
    def is_media(self) -> bool:
        """True if this message contains a media attachment.

        Returns:
            True for photo, video, audio, document, or voice messages.
        """
        # RU: True, если сообщение содержит медиавложение.
        return self.type in (
            MessageType.PHOTO,
            MessageType.VIDEO,
            MessageType.AUDIO,
            MessageType.DOCUMENT,
            MessageType.VOICE,
        )

    @property
    def is_reply(self) -> bool:
        """True if this message is a reply to another message.

        Returns:
            True when ``reply_to_message_id`` is set.
        """
        # RU: True, если это сообщение является ответом на другое.
        return self.reply_to_message_id is not None

    @property
    def is_forward(self) -> bool:
        """True if this message was forwarded from another chat.

        Returns:
            True when ``forward_from_chat_id`` is set.
        """
        # RU: True, если сообщение было переслано из другого чата.
        return self.forward_from_chat_id is not None

    @property
    def is_edited(self) -> bool:
        """True if this message has been edited after sending.

        Returns:
            True when ``edit_date`` is set.
        """
        # RU: True, если сообщение было отредактировано после отправки.
        return self.edit_date is not None

    def to_dict(self) -> dict:
        """Serialise the message to a plain dictionary.

        Returns:
            Dictionary with all fields; datetime values as ISO-8601 strings.
        """
        # RU: Сериализовать сообщение в словарь; даты в формате ISO-8601.
        return {
            "id": self.id,
            "chat_id": self.chat_id,
            "from_user_id": self.from_user_id,
            "type": self.type.value,
            "text": self.text,
            "caption": self.caption,
            "date": self.date.isoformat(),
            "edit_date": self.edit_date.isoformat() if self.edit_date else None,
            "reply_to_message_id": self.reply_to_message_id,
            "forward_from_chat_id": self.forward_from_chat_id,
            "media_url": self.media_url,
            "media_file_id": self.media_file_id,
        }
