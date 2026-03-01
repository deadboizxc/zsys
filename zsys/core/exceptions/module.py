"""Module and file-related exceptions."""

from .base import BaseException


class ModuleError(BaseException):
    """Module loading/operation errors."""
    pass


class FileError(BaseException):
    """File operation errors."""
    pass
