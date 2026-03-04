"""RSA cipher — asymmetric RSA-OAEP encryption implementing ICipher.

Wraps the ``cryptography`` hazmat layer for RSA with OAEP padding (SHA-256 MGF1).
Public key encrypts, private key decrypts. Supports PEM export of both keys.
Requires: pip install zsys[crypto].
"""
# RU: RSA-OAEP асимметричное шифрование через библиотеку cryptography.
# RU: Публичный ключ — шифрование, приватный — расшифровка. Требует pip install zsys[crypto].

from typing import Optional, Tuple
from zsys.core.interfaces import ICipher
from zsys.core.exceptions import CryptoError

try:
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.backends import default_backend

    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False


class RSACipher(ICipher):
    """
    RSA (Rivest–Shamir–Adleman) cipher implementation.

    Asymmetric encryption using RSA.
    Uses public key for encryption, private key for decryption.

    Install with:
        pip install zsys[crypto]

    Usage:
        # Generate new key pair
        cipher = RSACipher.generate()

        # Or load existing keys
        cipher = RSACipher(private_key=private_key, public_key=public_key)

        encrypted = cipher.encrypt(b"Hello, world!")
        decrypted = cipher.decrypt(encrypted)
    """

    def __init__(self, private_key=None, public_key=None):
        """
        Initialize RSA cipher.

        Args:
            private_key: RSA private key
            public_key: RSA public key
        """
        if not CRYPTOGRAPHY_AVAILABLE:
            raise CryptoError(
                "Cryptography library is not installed. "
                "Install with: pip install zsys[crypto]"
            )

        self.private_key = private_key
        self.public_key = public_key

    @classmethod
    def generate(cls, key_size: int = 2048) -> "RSACipher":
        """
        Generate new RSA key pair.

        Args:
            key_size: Key size in bits (default: 2048)

        Returns:
            New RSACipher instance with generated keys
        """
        private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=key_size, backend=default_backend()
        )
        public_key = private_key.public_key()

        return cls(private_key=private_key, public_key=public_key)

    def encrypt(self, data: bytes) -> bytes:
        """
        Encrypt data with public key.

        Args:
            data: Plain data to encrypt

        Returns:
            Encrypted data
        """
        if not self.public_key:
            raise CryptoError("Public key not set")

        encrypted = self.public_key.encrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        return encrypted

    def decrypt(self, data: bytes) -> bytes:
        """
        Decrypt data with private key.

        Args:
            data: Encrypted data

        Returns:
            Decrypted plain data
        """
        if not self.private_key:
            raise CryptoError("Private key not set")

        decrypted = self.private_key.decrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        return decrypted

    def encrypt_string(self, text: str, encoding: str = "utf-8") -> bytes:
        """Encrypt text string."""
        return self.encrypt(text.encode(encoding))

    def decrypt_string(self, data: bytes, encoding: str = "utf-8") -> str:
        """Decrypt to text string."""
        return self.decrypt(data).decode(encoding)

    def export_private_key(self) -> bytes:
        """Export private key to PEM format."""
        if not self.private_key:
            raise CryptoError("Private key not set")

        return self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

    def export_public_key(self) -> bytes:
        """Export public key to PEM format."""
        if not self.public_key:
            raise CryptoError("Public key not set")

        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )


__all__ = ["RSACipher"]
