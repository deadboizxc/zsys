"""BaseUser dataclass — platform-agnostic user model.

Represents a user in any messaging platform or system without ORM
or platform-specific dependencies.
"""
# RU: Датакласс BaseUser — платформо-независимая модель пользователя.
# RU: Для сохранения в БД используйте zsys.data.orm.user.BaseUser.

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class BaseUser:
    """Platform-agnostic base user model.

    Represents a user in memory without ORM or external dependencies.
    Can be extended by platform-specific subclasses (TelegramUser,
    DiscordUser, WebUser).

    Attributes:
        id: Unique numeric user identifier on the platform.
        username: Username without the leading ``@``; None if not set.
        first_name: User's first name; None if not available.
        last_name: User's last name; None if not available.
        is_bot: True if this account is a bot.
        is_premium: True if the user has premium/paid status.
        language_code: BCP-47 language code (e.g. ``"en"``, ``"ru"``); None if unknown.
        phone_number: Phone number in E.164 format; None if not available.
        created_at: Timestamp when this data record was created locally.
    """
    # RU: Платформо-независимая модель пользователя в памяти.

    id: int
    """Unique user ID"""

    username: Optional[str] = None
    """Username (without @)"""

    first_name: Optional[str] = None
    """User's first name"""

    last_name: Optional[str] = None
    """User's last name"""

    is_bot: bool = False
    """Whether this user is a bot"""

    is_premium: bool = False
    """Whether this user has premium status"""

    language_code: Optional[str] = None
    """User's language code (e.g., 'en', 'ru')"""

    phone_number: Optional[str] = None
    """User's phone number (if available)"""

    created_at: datetime = field(default_factory=datetime.now)
    """When this user record was created"""

    @property
    def full_name(self) -> str:
        """Concatenated first and last name, falling back gracefully.

        Returns:
            ``"First Last"`` when both names are set, ``"First"`` or
            ``"Last"`` if only one is available, or ``"Unknown User"``.
        """
        # RU: Полное имя из first_name + last_name с graceful fallback.
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return "Unknown User"

    @property
    def mention(self) -> str:
        """Platform mention string for use in message text.

        Returns:
            ``@username`` if username is set, otherwise :attr:`full_name`.
        """
        # RU: Строка упоминания пользователя для вставки в сообщения.
        if self.username:
            return f"@{self.username}"
        return self.full_name

    def to_dict(self) -> dict:
        """Serialise the user to a plain dictionary.

        Returns:
            Dictionary with all fields; ``created_at`` as ISO-8601 string.
        """
        # RU: Сериализовать пользователя в словарь; created_at в ISO-8601.
        return {
            "id": self.id,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "is_bot": self.is_bot,
            "is_premium": self.is_premium,
            "language_code": self.language_code,
            "phone_number": self.phone_number,
            "created_at": self.created_at.isoformat(),
        }
