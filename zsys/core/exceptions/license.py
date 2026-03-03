"""ZSYS license exceptions — licensing validation and activation errors.

Raised by the license manager when a license key is invalid, expired,
or cannot be activated.
"""
# RU: Исключения лицензирования — ошибки валидации и активации лицензии.
# RU: Возникают в менеджере лицензий при некорректных или истёкших ключах.

from .base import BaseException


class LicenseError(BaseException):
    """Exception raised when a license operation fails.

    Raised during license key validation, signature verification, or
    activation when the key is invalid, expired, revoked, or the
    license server is unreachable.

    Attributes:
        message: Human-readable error description.
        code: Optional error code (e.g. ``"LICENSE_EXPIRED"``).
    """

    # RU: Исключение при сбое операции с лицензией.
    pass
