"""ZSYS configuration exceptions — config loading and validation errors.

Raised when configuration values are missing, malformed, or fail
Pydantic validation.
"""
# RU: Исключения конфигурации — ошибки загрузки и валидации конфига.
# RU: Возникают при отсутствии, некорректных или невалидных значениях конфигурации.

from .base import BaseException


class ConfigError(BaseException):
    """Exception raised when configuration is invalid or cannot be loaded.

    Raised by BaseConfig and its subclasses when required environment
    variables are missing, values fail type validation, or .env files
    cannot be parsed.

    Attributes:
        message: Human-readable error description.
        code: Optional error code string.
    """

    # RU: Исключение при невалидной или не загружаемой конфигурации.
    pass


__all__ = [
    "ConfigError",
]
