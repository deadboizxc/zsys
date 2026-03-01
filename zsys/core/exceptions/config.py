"""Configuration-related exceptions."""

from .base import BaseException


class ConfigError(BaseException):
    """Configuration-related errors."""
    pass


__all__ = [
    "ConfigError",
]
