"""Storage and database exceptions."""

from .base import BaseException


class DatabaseError(BaseException):
    """Database operation errors."""
    pass


class StorageError(BaseException):
    """Storage operation errors."""
    pass


__all__ = [
    "DatabaseError",
    "StorageError",
]
