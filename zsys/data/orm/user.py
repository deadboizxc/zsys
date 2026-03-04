"""BaseUser model - unified user entity across all projects."""

from sqlalchemy import Boolean, Column, String

from .base import BaseModel


class BaseUser(BaseModel):
    """
    Base User model for the zsys ecosystem.

    Contains common user fields used across all services.
    Extend this class for service-specific user models.

    Example:
        from zsys.models import BaseUser
        from sqlalchemy import Column, String

        class TelegramUser(BaseUser):
            __tablename__ = "telegram_users"

            telegram_id = Column(String(50), unique=True)
    """

    __tablename__ = "users"

    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    is_bot = Column(Boolean, default=False)
    is_premium = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True, index=True)
    language_code = Column(String(10), default="en")

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        parts = [p for p in [self.first_name, self.last_name] if p]
        return " ".join(parts) if parts else self.username

    def __repr__(self) -> str:
        return f"<BaseUser(id={self.id}, username={self.username})>"


# Backward compatible alias
User = BaseUser

__all__ = ["BaseUser", "User"]
