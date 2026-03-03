"""AES cipher implementation — AES-256-CBC symmetric encryption.

Implements the ICipher interface using AES-256 in CBC mode with PKCS7
padding.  Each encrypt() call generates a fresh random IV that is
prepended to the ciphertext, so the output format is: IV (16 bytes) +
ciphertext.

Requires the ``cryptography`` package::

    pip install zsys[crypto]
"""
# RU: Реализация AES-шифра — симметричное шифрование AES-256-CBC.
# RU: IV (16 байт) предшествует шифртексту в выводе encrypt().

from typing import Optional
from core.interfaces import ICipher
from core.exceptions import CryptoError
import os
import hashlib

try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import padding

    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False


class AESCipher(ICipher):
    """AES-256-CBC symmetric cipher implementing the ICipher interface.

    Encrypts and decrypts arbitrary byte sequences using AES-256 in CBC mode
    with PKCS7 padding.  Each ``encrypt()`` call uses a fresh random 16-byte
    IV prepended to the ciphertext, so ``decrypt()`` extracts the IV from the
    first 16 bytes automatically.

    Requires ``pip install zsys[crypto]``.

    Example::

        cipher = AESCipher(key="my_secret_key")

        encrypted = cipher.encrypt(b"Hello, world!")
        decrypted = cipher.decrypt(encrypted)

        # Convenience string helpers
        enc = cipher.encrypt_string("Hello, world!")
        text = cipher.decrypt_string(enc)
    """

    # RU: Симметричный шифр AES-256-CBC. IV (16 байт) предшествует шифртексту.

    def __init__(self, key: str | bytes):
        """Initialise the cipher with a key of any length.

        The key is normalised to 32 bytes (AES-256) using SHA-256.

        Args:
            key: Encryption key as a string or raw bytes; any length is accepted.

        Raises:
            CryptoError: If the ``cryptography`` package is not installed.
        """
        # RU: Инициализировать шифр; ключ нормализуется до 32 байт через SHA-256.
        if not CRYPTOGRAPHY_AVAILABLE:
            raise CryptoError(
                "Cryptography library is not installed. "
                "Install with: pip install zsys[crypto]"
            )

        # Convert key to 32 bytes (for AES-256)
        if isinstance(key, str):
            key = key.encode()

        self.key = hashlib.sha256(key).digest()

    def encrypt(self, data: bytes) -> bytes:
        """Encrypt plaintext bytes using AES-256-CBC.

        Args:
            data: Plaintext bytes to encrypt.

        Returns:
            16-byte random IV concatenated with the PKCS7-padded ciphertext.
        """
        # RU: Зашифровать байты; вернуть IV (16 байт) + шифртекст.

        # Generate random IV
        iv = os.urandom(16)

        # Create cipher
        cipher = Cipher(
            algorithms.AES(self.key), modes.CBC(iv), backend=default_backend()
        )
        encryptor = cipher.encryptor()

        # Pad data to block size (16 bytes) using PKCS7
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(data) + padder.finalize()

        # Encrypt and prepend IV
        encrypted = encryptor.update(padded_data) + encryptor.finalize()

        # Return IV + encrypted data
        return iv + encrypted

    def decrypt(self, data: bytes) -> bytes:
        """Decrypt ciphertext bytes produced by :meth:`encrypt`.

        Args:
            data: Bytes in the format ``IV (16 bytes) + ciphertext``.

        Returns:
            Original plaintext bytes with PKCS7 padding removed.
        """
        # RU: Расшифровать байты формата «IV + шифртекст»; удалить PKCS7-паддинг.

        # Extract IV and encrypted data
        iv = data[:16]
        encrypted = data[16:]

        # Create cipher
        cipher = Cipher(
            algorithms.AES(self.key), modes.CBC(iv), backend=default_backend()
        )
        decryptor = cipher.decryptor()

        # Decrypt, then remove PKCS7 padding
        padded_data = decryptor.update(encrypted) + decryptor.finalize()

        # Unpad
        unpadder = padding.PKCS7(128).unpadder()
        data = unpadder.update(padded_data) + unpadder.finalize()

        return data

    def encrypt_string(self, text: str, encoding: str = "utf-8") -> bytes:
        """Encode *text* and encrypt it.

        Args:
            text: Plaintext string.
            encoding: Character encoding for the string-to-bytes conversion.

        Returns:
            Encrypted bytes (IV + ciphertext).
        """
        # RU: Закодировать строку и зашифровать.
        return self.encrypt(text.encode(encoding))

    def decrypt_string(self, data: bytes, encoding: str = "utf-8") -> str:
        """Decrypt ciphertext bytes and decode to a string.

        Args:
            data: Encrypted bytes (IV + ciphertext).
            encoding: Character encoding for the bytes-to-string conversion.

        Returns:
            Decrypted plaintext string.
        """
        # RU: Расшифровать байты и декодировать в строку.
        return self.decrypt(data).decode(encoding)


__all__ = ["AESCipher"]
