"""ZSYS validation exceptions — data validation errors.

Raised when input data fails schema, type, or business-rule validation.
"""
# RU: Исключения валидации — ошибки проверки входных данных.
# RU: Возникают при несоответствии данных схеме, типам или бизнес-правилам.

from typing import Any, Dict, Optional

from .base import BaseException


class ValidationError(BaseException):
    """Exception raised when data fails validation rules.

    Raised by Pydantic models, form handlers, and business-logic validators
    when a value does not conform to expected constraints.

    Attributes:
        message: Human-readable error description.
        code: Always ``"VALIDATION_ERROR"`` for consistent programmatic handling.
        field: Name of the field that failed validation, if applicable.
        details: Additional context dictionary (e.g. constraints violated).
    """

    # RU: Исключение при нарушении правил валидации данных.

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialise the validation error.

        Args:
            message: Human-readable description of what failed validation.
            field: Name of the field that caused the error (optional).
            details: Additional structured context (optional).
        """
        # RU: Инициализировать с описанием ошибки, именем поля и деталями.
        super().__init__(message, code="VALIDATION_ERROR", details=details)
        self.field = field


__all__ = [
    "ValidationError",
]
