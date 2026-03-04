"""ZSYS base exception — root of the entire exception hierarchy.

Provides BaseException with optional error codes, structured detail
dictionaries, and rich string formatting used by all ZSYS exceptions.
"""
# RU: Базовое исключение ZSYS — корень иерархии исключений.
# RU: Поддерживает коды ошибок, словари деталей и форматированный вывод.

from typing import Any, Dict, Optional


class BaseException(Exception):
    """Root exception class for all ZSYS errors.

    All domain-specific exceptions (ConfigError, NetworkError, etc.)
    inherit from this class.  Provides an optional machine-readable
    ``code`` and a ``details`` dictionary for structured context.

    Attributes:
        message: Human-readable error description.
        code: Optional machine-readable error code (e.g. ``"INVALID_TOKEN"``).
        details: Dictionary of additional structured error context.
    """

    # RU: Корневой класс исключений ZSYS. Все остальные исключения наследуют его.

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialise the exception with a message, optional code and details.

        Args:
            message: Human-readable error description.
            code: Optional machine-readable error code (e.g. ``"INVALID_TOKEN"``).
            details: Optional mapping of additional structured error context.
        """
        # RU: Инициализировать исключение с сообщением, опциональным кодом и деталями.
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

    def __str__(self) -> str:
        """Return a human-readable string, prefixed with code when present.

        Returns:
            ``"[CODE] message"`` if code is set, otherwise just ``"message"``.
        """
        # RU: Вернуть строку вида «[КОД] сообщение» или просто «сообщение».
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message

    def __repr__(self) -> str:
        """Return an unambiguous debug representation.

        Returns:
            String with class name, message, and code for debugging.
        """
        # RU: Вернуть отладочное представление с именем класса, сообщением и кодом.
        return (
            f"{self.__class__.__name__}(message={self.message!r}, code={self.code!r})"
        )


__all__ = [
    "BaseException",
]
