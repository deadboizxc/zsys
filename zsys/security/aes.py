"""AES cipher — symmetric AES-256-CBC encryption implementing ICipher.

Wraps the ``cryptography`` package (hazmat layer) to provide AES-256 in CBC mode
with PKCS7 padding. Key material is normalised to 32 bytes via SHA-256.
Requires: pip install zsys[crypto]  (cryptography>=3.0).
"""
# RU: AES-256-CBC шифрование через библиотеку cryptography.
# RU: Ключ нормализуется до 32 байт через SHA-256; требует pip install zsys[crypto].

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
    """
    AES (Advanced Encryption Standard) cipher implementation.
    
    Symmetric encryption using AES-256 in CBC mode.
    
    Install with:
        pip install zsys[crypto]
    
    Usage:
        cipher = AESCipher(key="my_secret_key")
        
        encrypted = cipher.encrypt(b"Hello, world!")
        decrypted = cipher.decrypt(encrypted)
        
        # Or use string methods
        encrypted = cipher.encrypt_string("Hello, world!")
        text = cipher.decrypt_string(encrypted)
    """
    
    def __init__(self, key: str | bytes):
        """
        Initialize AES cipher.
        
        Args:
            key: Encryption key (string or bytes)
        """
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
        """
        Encrypt data.
        
        Args:
            data: Plain data to encrypt
            
        Returns:
            IV (16 bytes) + encrypted data
        """
        # Generate random IV
        iv = os.urandom(16)
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        # Pad data to block size (16 bytes)
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(data) + padder.finalize()
        
        # Encrypt
        encrypted = encryptor.update(padded_data) + encryptor.finalize()
        
        # Return IV + encrypted data
        return iv + encrypted
    
    def decrypt(self, data: bytes) -> bytes:
        """
        Decrypt data.
        
        Args:
            data: IV + encrypted data
            
        Returns:
            Decrypted plain data
        """
        # Extract IV and encrypted data
        iv = data[:16]
        encrypted = data[16:]
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.CBC(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        # Decrypt
        padded_data = decryptor.update(encrypted) + decryptor.finalize()
        
        # Unpad
        unpadder = padding.PKCS7(128).unpadder()
        data = unpadder.update(padded_data) + unpadder.finalize()
        
        return data
    
    def encrypt_string(self, text: str, encoding: str = "utf-8") -> bytes:
        """Encrypt text string."""
        return self.encrypt(text.encode(encoding))
    
    def decrypt_string(self, data: bytes, encoding: str = "utf-8") -> str:
        """Decrypt to text string."""
        return self.decrypt(data).decode(encoding)


__all__ = ["AESCipher"]
