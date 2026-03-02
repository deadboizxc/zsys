"""ZSYS blockchain exceptions — chain and transaction errors.

Raised by IBlockchain and IWallet implementations when blockchain
operations or transactions fail.
"""
# RU: Исключения блокчейна — ошибки цепочки и транзакций.
# RU: Возникают при сбоях операций IBlockchain и IWallet.

from .base import BaseException


class BlockchainError(BaseException):
    """Exception raised when a blockchain operation fails.

    Covers connection failures, invalid blocks, consensus errors,
    and any other chain-level problem.

    Attributes:
        message: Human-readable error description.
        code: Optional error code string.
    """
    # RU: Исключение при сбое операции блокчейна.
    pass


class TransactionError(BlockchainError):
    """Exception raised when a transaction fails to be created, signed, or sent.

    Inherits from BlockchainError so callers can catch either.
    Raised for insufficient funds, invalid address, network rejection, etc.

    Attributes:
        message: Human-readable error description.
        code: Optional error code string.
    """
    # RU: Исключение при сбое транзакции (создание, подпись или отправка).
    pass


__all__ = [
    "BlockchainError",
    "TransactionError",
]
