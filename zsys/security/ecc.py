"""ECC cipher — ECDH key exchange with AES-GCM encryption implementing ICipher.

Uses SECP256R1 curve for Elliptic-Curve Diffie-Hellman to derive a shared secret,
then HKDF-SHA256 to produce a 32-byte AES key, and AES-GCM for authenticated
encryption. More efficient than RSA at equivalent security levels.
Requires: pip install zsys[crypto].
"""
# RU: ECC-шифрование через ECDH + AES-GCM; кривая SECP256R1.
# RU: Эффективнее RSA при эквивалентном уровне безопасности. Требует pip install zsys[crypto].

from core.interfaces import ICipher
from core.exceptions import CryptoError

try:
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.backends import default_backend

    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False

import os


class ECCCipher(ICipher):
    """
    ECC (Elliptic Curve Cryptography) cipher implementation.

    Uses ECDH for key agreement and AES-GCM for encryption.
    More efficient than RSA with similar security level.

    Install with:
        pip install zsys[crypto]

    Usage:
        # Generate new key pair
        cipher = ECCCipher.generate()

        encrypted = cipher.encrypt(b"Hello, world!")
        decrypted = cipher.decrypt(encrypted)
    """

    def __init__(self, private_key=None, public_key=None):
        """
        Initialize ECC cipher.

        Args:
            private_key: ECC private key
            public_key: ECC public key
        """
        if not CRYPTOGRAPHY_AVAILABLE:
            raise CryptoError(
                "Cryptography library is not installed. "
                "Install with: pip install zsys[crypto]"
            )

        self.private_key = private_key
        self.public_key = public_key

    @classmethod
    def generate(cls, curve=None) -> "ECCCipher":
        """
        Generate new ECC key pair.

        Args:
            curve: Elliptic curve (default: SECP256R1)

        Returns:
            New ECCCipher instance with generated keys
        """
        if curve is None:
            curve = ec.SECP256R1()

        private_key = ec.generate_private_key(curve, default_backend())
        public_key = private_key.public_key()

        return cls(private_key=private_key, public_key=public_key)

    def _derive_key(self, shared_secret: bytes) -> bytes:
        """Derive encryption key from shared secret."""
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b"handshake data",
            backend=default_backend(),
        )
        return hkdf.derive(shared_secret)

    def encrypt(self, data: bytes) -> bytes:
        """
        Encrypt data.

        Note: For ECC, we use ephemeral key exchange.
        Returns: ephemeral_public_key + nonce + ciphertext
        """
        if not self.public_key:
            raise CryptoError("Public key not set")

        # Generate ephemeral key pair
        ephemeral_private = ec.generate_private_key(ec.SECP256R1(), default_backend())
        ephemeral_public = ephemeral_private.public_key()

        # Perform ECDH
        shared_key = ephemeral_private.exchange(ec.ECDH(), self.public_key)

        # Derive encryption key
        key = self._derive_key(shared_key)

        # Encrypt with AES-GCM
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, data, None)

        # Serialize ephemeral public key
        ephemeral_public_bytes = ephemeral_public.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint,
        )

        # Return ephemeral_public + nonce + ciphertext
        return ephemeral_public_bytes + nonce + ciphertext

    def decrypt(self, data: bytes) -> bytes:
        """
        Decrypt data.

        Args:
            data: ephemeral_public_key + nonce + ciphertext
        """
        if not self.private_key:
            raise CryptoError("Private key not set")

        # Extract components
        # SECP256R1 uncompressed point is 65 bytes
        ephemeral_public_bytes = data[:65]
        nonce = data[65:77]  # 12 bytes
        ciphertext = data[77:]

        # Deserialize ephemeral public key
        ephemeral_public = ec.EllipticCurvePublicKey.from_encoded_point(
            ec.SECP256R1(), ephemeral_public_bytes
        )

        # Perform ECDH
        shared_key = self.private_key.exchange(ec.ECDH(), ephemeral_public)

        # Derive encryption key
        key = self._derive_key(shared_key)

        # Decrypt with AES-GCM
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)

        return plaintext

    def encrypt_string(self, text: str, encoding: str = "utf-8") -> bytes:
        """Encrypt text string."""
        return self.encrypt(text.encode(encoding))

    def decrypt_string(self, data: bytes, encoding: str = "utf-8") -> str:
        """Decrypt to text string."""
        return self.decrypt(data).decode(encoding)


__all__ = ["ECCCipher"]
