"""IChat — abstract contract for chat/conversation representations.

Defines the structural Protocol interface for platform-agnostic chat
objects: private chats, groups, supergroups, and channels.
"""
# RU: Интерфейс IChat — контракт для представления чатов и переписок.
# RU: Охватывает личные чаты, группы, супергруппы и каналы.

from typing import Protocol, runtime_checkable, Any
from enum import Enum


class ChatType(str, Enum):
    """Enumeration of supported chat types across messaging platforms.

    Values are lowercase strings to allow direct comparison with
    platform API responses.
    """
    # RU: Перечисление типов чатов на платформах обмена сообщениями.
    PRIVATE = "private"
    GROUP = "group"
    SUPERGROUP = "supergroup"
    CHANNEL = "channel"
    BOT = "bot"


@runtime_checkable
class IChat(Protocol):
    """Abstract contract for chat/conversation objects.

    Represents any conversation — private, group, channel — in a
    platform-agnostic way.  Implementations must expose identity
    properties and messaging operations.

    Supported platforms:
        - Telegram (private chats, groups, channels)
        - Discord channels
        - Any other messaging platform
    """
    # RU: Абстрактный контракт для объектов чата/переписки.

    @property
    def id(self) -> int:
        """Platform-unique numeric identifier of the chat.

        Returns:
            Chat ID as an integer (negative for groups/channels on Telegram).
        """
        # RU: Уникальный числовой идентификатор чата на платформе.
        ...

    @property
    def title(self) -> str | None:
        """Human-readable title of the chat.

        Returns:
            Title string for groups/channels, or None for private chats.
        """
        # RU: Название чата (для групп/каналов), None для личных чатов.
        ...

    @property
    def type(self) -> ChatType:
        """Category of this chat.

        Returns:
            One of the ChatType enum values.
        """
        # RU: Тип чата (личный, группа, канал и т.д.).
        ...

    @property
    def username(self) -> str | None:
        """Public username of the chat, if any.

        Returns:
            Username string without the leading ``@``, or None.
        """
        # RU: Публичное имя пользователя чата без символа @, если есть.
        ...

    async def send_message(self, text: str, **kwargs: Any) -> Any:
        """Send a text message to this chat.

        Args:
            text: UTF-8 message text.
            **kwargs: Platform-specific parameters (parse_mode, etc.).

        Returns:
            Platform-specific sent message object.
        """
        # RU: Отправить текстовое сообщение в этот чат.
        ...

    async def get_member(self, user_id: int) -> Any:
        """Retrieve membership information for a user in this chat.

        Args:
            user_id: Numeric user identifier to look up.

        Returns:
            Platform-specific chat member object.
        """
        # RU: Получить информацию об участнике чата по идентификатору.
        ...

    async def get_members_count(self) -> int:
        """Return the total number of members in this chat.

        Returns:
            Member count as an integer.
        """
        # RU: Вернуть общее количество участников чата.
        ...


__all__ = [
    "IChat",
    "ChatType",
]
