"""ZSYS network exceptions — connection and timeout errors.

Raised by transport layers and HTTP clients when network-level
operations fail or exceed time limits.
"""
# RU: Исключения сети — ошибки соединения и превышения времени ожидания.
# RU: Возникают в транспортном слое и HTTP-клиентах при сетевых сбоях.

from .base import BaseException


class NetworkError(BaseException):
    """Exception raised when a network connection or request fails.

    Raised for DNS failures, refused connections, TLS handshake errors,
    and other low-level networking problems.

    Attributes:
        message: Human-readable error description.
        code: Optional error code string.
    """

    # RU: Исключение при сбое сетевого соединения или запроса.
    pass


class TimeoutError(BaseException):
    """Exception raised when an operation exceeds its time limit.

    Raised by HTTP clients and async tasks when a configurable deadline
    is exceeded while waiting for a response.

    Attributes:
        message: Human-readable error description.
        code: Optional error code string.
    """

    # RU: Исключение при превышении времени ожидания операции.
    pass


__all__ = [
    "NetworkError",
    "TimeoutError",
]
