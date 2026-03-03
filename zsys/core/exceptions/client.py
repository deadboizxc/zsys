"""ZSYS client exceptions — client, authentication, and session errors.

Raised by bot and userbot client implementations when lifecycle,
authentication, or session operations fail.
"""
# RU: Исключения клиента — ошибки клиента, аутентификации и сессий.
# RU: Возникают при сбоях жизненного цикла, аутентификации или работы с сессией.

from .base import BaseException


class ClientError(BaseException):
    """Exception raised when a bot or userbot client operation fails.

    Raised by start/stop lifecycle methods, message sending, and other
    client-level operations that encounter platform errors.

    Attributes:
        message: Human-readable error description.
        code: Optional platform-specific error code.
    """

    # RU: Исключение при сбое операции бот- или юзербот-клиента.
    pass


class AuthenticationError(BaseException):
    """Exception raised when authentication or authorisation fails.

    Raised when API credentials (token, api_id/api_hash, session) are
    invalid, expired, or revoked by the platform.

    Attributes:
        message: Human-readable error description.
        code: Optional error code (e.g. ``"INVALID_TOKEN"``).
    """

    # RU: Исключение при сбое аутентификации или авторизации.
    pass


class SessionError(BaseException):
    """Exception raised when session management fails.

    Raised for corrupted session files, expired sessions, or conflicts
    when attempting to resume or create a new session.

    Attributes:
        message: Human-readable error description.
        code: Optional error code string.
    """

    # RU: Исключение при сбое управления сессией.
    pass


__all__ = [
    "ClientError",
    "AuthenticationError",
    "SessionError",
]
