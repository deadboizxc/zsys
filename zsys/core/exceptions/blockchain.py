"""Blockchain and transaction exceptions."""

from .base import BaseException


class BlockchainError(BaseException):
    """Blockchain operation errors."""
    pass


class TransactionError(BlockchainError):
    """Transaction-related errors."""
    pass


__all__ = [
    "BlockchainError",
    "TransactionError",
]
