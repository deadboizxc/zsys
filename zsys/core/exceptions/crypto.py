"""ZSYS cryptography exceptions — cipher and key-management errors.

Raised by ICipher implementations (AES, RSA, ECC) when encryption,
decryption, or key operations fail.
"""
# RU: Исключения криптографии — ошибки шифрования и управления ключами.
# RU: Возникают в реализациях ICipher (AES, RSA, ECC) при сбоях операций.

from .base import BaseException


class CryptoError(BaseException):
    """Exception raised when a cryptographic operation fails.

    Raised by AESCipher, RSACipher, ECCCipher and related utilities for
    missing keys, decryption failures, padding errors, or unavailable
    cryptography library.

    Attributes:
        message: Human-readable error description.
        code: Optional error code string.
    """
    # RU: Исключение при сбое криптографической операции.
    pass


__all__ = [
    "CryptoError",
]
