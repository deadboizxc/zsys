"""ZSYS API and bot exceptions — HTTP and bot-operation errors.

Raised when external API calls fail or bot operations encounter
platform-level errors.
"""
# RU: Исключения API и бота — ошибки HTTP-запросов и операций бота.
# RU: Возникают при сбоях внешних API или платформенных ошибках бота.

from .base import BaseException


class APIError(BaseException):
    """Exception raised when an API or HTTP request fails.

    Raised by HTTP transport layers and external API adapters when the
    remote server returns an error or the request cannot be completed.

    Attributes:
        message: Human-readable error description.
        code: Optional error code — may be an HTTP status as a string
            (e.g. ``"404"``) or a platform-specific error code.
    """

    # RU: Исключение при сбое API- или HTTP-запроса.

    def __init__(self, message: str, code: str | None = None):
        """Initialise the API error.

        Args:
            message: Human-readable error description.
            code: Optional error code (HTTP status string or platform code).
        """
        # RU: Инициализировать ошибку API с сообщением и опциональным кодом.
        super().__init__(message, code)


class BotError(BaseException):
    """Exception raised when a bot-level operation fails.

    Raised for platform errors that are not HTTP-level (e.g. rate limits,
    invalid bot token, permission denied by platform).

    Attributes:
        message: Human-readable error description.
        code: Optional platform-specific error code.
    """

    # RU: Исключение при сбое операции на уровне бота.
    pass
