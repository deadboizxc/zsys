"""Security domain — placeholder for domain-level security models.

Reserved for future security domain entities such as permission models,
roles, policies, and security context objects used across the zsys security layer.
"""
# RU: Домен безопасности — заглушка для будущих моделей и объектов безопасности.
# RU: Зарезервировано для прав доступа, ролей и политик безопасности.
import hashlib
import hmac
import os
import time
from typing import Optional

try:
    from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
    HAS_CHACHA = True
except ImportError:
    HAS_CHACHA = False


def compute_file_hash(data: bytes) -> str:
    """Compute SHA-256 hash of file data."""
    return hashlib.sha256(data).hexdigest()


def generate_token(user_id: str, secret: str, timestamp: Optional[int] = None) -> str:
    """Generate authentication token."""
    if timestamp is None:
        timestamp = int(time.time())
    payload = f"{user_id}:{timestamp}"
    signature = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return f"{payload}:{signature}"


def verify_token(token: str, secret: str, ttl: int = 86400) -> Optional[str]:
    """Verify token and return user_id if valid."""
    try:
        parts = token.split(":")
        if len(parts) != 3:
            return None
        user_id, timestamp_str, signature = parts
        timestamp = int(timestamp_str)
        
        # Check expiration
        if time.time() - timestamp > ttl:
            return None
        
        # Verify signature
        expected_payload = f"{user_id}:{timestamp_str}"
        expected_sig = hmac.new(
            secret.encode(),
            expected_payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if hmac.compare_digest(signature, expected_sig):
            return user_id
        return None
    except (ValueError, TypeError):
        return None


class ChaChaEncryption:
    """ChaCha20-Poly1305 encryption for RPC payloads."""
    
    def __init__(self, key: bytes):
        if not HAS_CHACHA:
            raise RuntimeError("cryptography package required for ChaCha20")
        if len(key) != 32:
            raise ValueError("Key must be 32 bytes")
        self._cipher = ChaCha20Poly1305(key)
    
    def encrypt(self, plaintext: bytes) -> bytes:
        """Encrypt data. Returns nonce + ciphertext."""
        nonce = os.urandom(12)
        ciphertext = self._cipher.encrypt(nonce, plaintext, None)
        return nonce + ciphertext
    
    def decrypt(self, data: bytes) -> bytes:
        """Decrypt data. Expects nonce + ciphertext."""
        if len(data) < 12:
            raise ValueError("Invalid encrypted data")
        nonce = data[:12]
        ciphertext = data[12:]
        return self._cipher.decrypt(nonce, ciphertext, None)
