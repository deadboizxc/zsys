"""Cryptography exceptions."""

from .base import BaseException


class CryptoError(BaseException):
    """Cryptography operation errors."""
    pass


__all__ = [
    "CryptoError",
]
