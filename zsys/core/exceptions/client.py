"""Client and authentication exceptions."""

from .base import BaseException


class ClientError(BaseException):
    """Client operation errors (bot/userbot)."""
    pass


class AuthenticationError(BaseException):
    """Authentication/authorization errors."""
    pass


class SessionError(BaseException):
    """Session management errors."""
    pass


__all__ = [
    "ClientError",
    "AuthenticationError",
    "SessionError",
]
