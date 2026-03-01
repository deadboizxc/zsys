"""Cipher interface for encryption/decryption."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class ICipher(Protocol):
    """
    Cipher interface for encryption/decryption.
    
    Can be implemented by:
    - AES (symmetric encryption)
    - RSA (asymmetric encryption)
    - ECC (elliptic curve cryptography)
    - ChaCha20 (modern stream cipher)
    """
    
    def encrypt(self, data: bytes) -> bytes:
        """
        Encrypt data.
        
        Args:
            data: Plain data to encrypt
            
        Returns:
            Encrypted data
        """
        ...
    
    def decrypt(self, data: bytes) -> bytes:
        """
        Decrypt data.
        
        Args:
            data: Encrypted data
            
        Returns:
            Decrypted plain data
        """
        ...
    
    def encrypt_string(self, text: str, encoding: str = "utf-8") -> bytes:
        """
        Encrypt text string.
        
        Args:
            text: Plain text to encrypt
            encoding: Text encoding (default: utf-8)
            
        Returns:
            Encrypted data
        """
        ...
    
    def decrypt_string(self, data: bytes, encoding: str = "utf-8") -> str:
        """
        Decrypt to text string.
        
        Args:
            data: Encrypted data
            encoding: Text encoding (default: utf-8)
            
        Returns:
            Decrypted text
        """
        ...


__all__ = [
    "ICipher",
]
