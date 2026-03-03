"""BaseChat dataclass — platform-agnostic chat/conversation model.

Represents any type of conversation (private, group, channel) without
ORM or platform-specific dependencies.
"""
# RU: Датакласс BaseChat — платформо-независимая модель чата/переписки.
# RU: Охватывает личные чаты, группы, каналы без зависимостей от ORM.

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from enum import Enum


# TODO: Move to core.interfaces.chat when interfaces module is created
class ChatType(str, Enum):
    """Enumeration of supported chat categories.

    String values match the platform API response strings directly.
    """

    # RU: Перечисление поддерживаемых типов чатов.
    PRIVATE = "private"
    GROUP = "group"
    SUPERGROUP = "supergroup"
    CHANNEL = "channel"
    BOT = "bot"


@dataclass
class BaseChat:
    """Platform-agnostic base chat model.

    Represents any conversation without ORM or external dependencies.
    Can be extended by platform-specific subclasses such as TelegramChat,
    DiscordChannel, or WebChatRoom.

    Attributes:
        id: Unique numeric chat identifier (negative for groups/channels on Telegram).
        type: Category of the chat (private, group, channel, etc.).
        title: Display title for groups/channels; None for private chats.
        username: Public @username without the leading ``@``; None if not public.
        description: Optional text description of the chat.
        members_count: Total number of members; None if not available.
        is_verified: Whether the chat has a platform verification badge.
        is_restricted: Whether the chat has content restrictions applied.
        created_at: Timestamp when this data record was created locally.
    """

    # RU: Платформо-независимая модель чата в памяти.

    id: int
    """Unique chat ID"""

    type: ChatType
    """Chat type (private, group, channel, etc.)"""

    title: Optional[str] = None
    """Chat title (for groups/channels)"""

    username: Optional[str] = None
    """Chat username (if public)"""

    description: Optional[str] = None
    """Chat description"""

    members_count: Optional[int] = None
    """Total members count"""

    is_verified: bool = False
    """Whether this chat is verified"""

    is_restricted: bool = False
    """Whether this chat is restricted"""

    created_at: datetime = field(default_factory=datetime.now)
    """When this chat record was created"""

    @property
    def is_private(self) -> bool:
        """True if this is a one-on-one private chat.

        Returns:
            True when type is ``ChatType.PRIVATE``.
        """
        # RU: True, если это личный (приватный) чат.
        return self.type == ChatType.PRIVATE

    @property
    def is_group(self) -> bool:
        """True if this chat is a group or supergroup.

        Returns:
            True when type is ``GROUP`` or ``SUPERGROUP``.
        """
        # RU: True, если это группа или супергруппа.
        return self.type in (ChatType.GROUP, ChatType.SUPERGROUP)

    @property
    def is_channel(self) -> bool:
        """True if this chat is a broadcast channel.

        Returns:
            True when type is ``ChatType.CHANNEL``.
        """
        # RU: True, если это канал (broadcast channel).
        return self.type == ChatType.CHANNEL

    @property
    def display_name(self) -> str:
        """Best human-readable name for display purposes.

        Returns:
            ``title`` if set, ``@username`` if available, or ``"Chat <id>"``.
        """
        # RU: Лучшее отображаемое имя: заголовок, @username или «Chat <id>».
        if self.title:
            return self.title
        elif self.username:
            return f"@{self.username}"
        return f"Chat {self.id}"

    def to_dict(self) -> dict:
        """Serialise the chat to a plain dictionary.

        Returns:
            Dictionary with all fields; ``created_at`` as ISO-8601 string.
        """
        # RU: Сериализовать чат в словарь; created_at в формате ISO-8601.
        return {
            "id": self.id,
            "type": self.type.value,
            "title": self.title,
            "username": self.username,
            "description": self.description,
            "members_count": self.members_count,
            "is_verified": self.is_verified,
            "is_restricted": self.is_restricted,
            "created_at": self.created_at.isoformat(),
        }
