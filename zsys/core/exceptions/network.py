"""Network and timeout exceptions."""

from .base import BaseException


class NetworkError(BaseException):
    """Network/connection errors."""
    pass


class TimeoutError(BaseException):
    """Timeout errors."""
    pass


__all__ = [
    "NetworkError",
    "TimeoutError",
]
