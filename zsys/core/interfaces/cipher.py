"""ICipher — abstract contract for encryption/decryption implementations.

Defines the structural Protocol interface that all cipher backends
(AES, RSA, ECC, ChaCha20, etc.) must satisfy.
"""
# RU: Интерфейс ICipher — контракт для реализаций шифрования/дешифрования.
# RU: Все бэкенды (AES, RSA, ECC и др.) должны соответствовать этому протоколу.

from typing import Protocol, runtime_checkable


@runtime_checkable
class ICipher(Protocol):
    """Abstract contract for symmetric and asymmetric cipher implementations.

    All cipher backends must expose byte-level and string-level
    encrypt/decrypt operations.  Implementations guarantee that
    ``decrypt(encrypt(data)) == data`` for any valid input.

    Supported implementations:
        - AES-256-CBC (symmetric, ``zsys.crypto.aes``)
        - RSA-OAEP (asymmetric, ``zsys.crypto.rsa``)
        - ECDH + AES-GCM (elliptic curve, ``zsys.crypto.ecc``)
        - ChaCha20-Poly1305 (stream cipher, future)
    """

    # RU: Абстрактный контракт для симметричных и асимметричных шифров.

    def encrypt(self, data: bytes) -> bytes:
        """Encrypt raw bytes and return the ciphertext.

        Implementations must produce output that can be round-tripped
        through :meth:`decrypt` to recover the original plaintext.

        Args:
            data: Plaintext bytes to encrypt.

        Returns:
            Ciphertext bytes (format is implementation-specific; may
            include IV, nonce, or ephemeral key prefix).

        Raises:
            CryptoError: If encryption fails (missing key, invalid data).
        """
        # RU: Зашифровать байты и вернуть шифртекст.
        ...

    def decrypt(self, data: bytes) -> bytes:
        """Decrypt ciphertext bytes and return the plaintext.

        Args:
            data: Ciphertext bytes previously produced by :meth:`encrypt`.

        Returns:
            Recovered plaintext bytes.

        Raises:
            CryptoError: If decryption fails (wrong key, corrupted data).
        """
        # RU: Расшифровать шифртекст и вернуть исходные байты.
        ...

    def encrypt_string(self, text: str, encoding: str = "utf-8") -> bytes:
        """Encode *text* to bytes and encrypt.

        Convenience wrapper that calls ``encrypt(text.encode(encoding))``.

        Args:
            text: Plaintext string to encrypt.
            encoding: Character encoding used to convert the string to bytes.

        Returns:
            Ciphertext bytes.

        Raises:
            CryptoError: If encryption fails.
        """
        # RU: Закодировать строку в байты и зашифровать.
        ...

    def decrypt_string(self, data: bytes, encoding: str = "utf-8") -> str:
        """Decrypt ciphertext bytes and decode to a string.

        Convenience wrapper that calls ``decrypt(data).decode(encoding)``.

        Args:
            data: Ciphertext bytes to decrypt.
            encoding: Character encoding used to decode the decrypted bytes.

        Returns:
            Decrypted plaintext string.

        Raises:
            CryptoError: If decryption fails.
        """
        # RU: Расшифровать шифртекст и декодировать в строку.
        ...


__all__ = [
    "ICipher",
]
