"""Resource access exceptions."""

from .base import BaseException


class NotFoundError(BaseException):
    """Resource not found errors."""
    pass


class PermissionError(BaseException):
    """Permission/access denied errors."""
    pass


class PermissionDeniedError(BaseException):
    """Permission denied with action context."""
    
    def __init__(self, action: str, code: str | None = None):
        message = f"Permission denied: {action}"
        super().__init__(message, code)
        self.action = action


__all__ = [
    "NotFoundError",
    "PermissionError",
    "PermissionDeniedError",
]
