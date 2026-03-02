"""Security crypto utilities — hashing, HMAC tokens, and ChaCha20 encryption.

Lightweight crypto helpers used internally by zsys security layer.
Provides SHA-256 file hashing, HMAC token generation/verification,
and optional ChaCha20-Poly1305 authenticated encryption.
Requires: pip install cryptography  for ChaCha20 support.
"""
# RU: Утилиты безопасности — хеширование, HMAC-токены и ChaCha20-шифрование.
# RU: ChaCha20 требует: pip install cryptography.

import hashlib
import hmac
import os
import time
from typing import Optional, Union

__all__ = [
    # Hashing
    'compute_hash',
    'compute_file_hash',
    'md5', 'sha256', 'sha512',
    # Tokens
    'generate_token',
    'verify_token',
    # ChaCha20
    'ChaChaEncryption',
    'HAS_CHACHA',
    # Argon2
    'hash_password',
    'verify_password',
    'HAS_ARGON2',
]

# Optional dependency checks
try:
    from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
    HAS_CHACHA = True
except ImportError:
    HAS_CHACHA = False

try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError
    HAS_ARGON2 = True
except ImportError:
    HAS_ARGON2 = False


# =============================================================================
# HASHING
# =============================================================================

def md5(data: Union[str, bytes]) -> str:
    """Compute MD5 hash."""
    if isinstance(data, str):
        data = data.encode()
    return hashlib.md5(data).hexdigest()


def sha256(data: Union[str, bytes]) -> str:
    """Compute SHA-256 hash."""
    if isinstance(data, str):
        data = data.encode()
    return hashlib.sha256(data).hexdigest()


def sha512(data: Union[str, bytes]) -> str:
    """Compute SHA-512 hash."""
    if isinstance(data, str):
        data = data.encode()
    return hashlib.sha512(data).hexdigest()


def compute_hash(data: Union[str, bytes], algorithm: str = "sha256") -> str:
    """
    Compute hash with specified algorithm.
    
    Args:
        data: Data to hash
        algorithm: Hash algorithm (md5, sha256, sha512)
        
    Returns:
        Hex digest of hash
    """
    if isinstance(data, str):
        data = data.encode()
    
    algorithms = {
        "md5": hashlib.md5,
        "sha256": hashlib.sha256,
        "sha512": hashlib.sha512,
    }
    
    func = algorithms.get(algorithm.lower())
    if not func:
        raise ValueError(f"Unsupported algorithm: {algorithm}")
    
    return func(data).hexdigest()


def compute_file_hash(
    data_or_path: Union[str, bytes, "Path"],
    algorithm: str = "sha256",
) -> str:
    """
    Compute hash of file contents or raw bytes.
    
    Args:
        data_or_path: Raw bytes data, or file path (str/Path) to hash
        algorithm: Hash algorithm (md5, sha256, sha512)
        
    Returns:
        Hex digest of hash
    """
    algorithms = {
        "md5": hashlib.md5,
        "sha256": hashlib.sha256,
        "sha512": hashlib.sha512,
    }
    
    func = algorithms.get(algorithm.lower())
    if not func:
        raise ValueError(f"Unsupported algorithm: {algorithm}")
    
    # If raw bytes — hash directly
    if isinstance(data_or_path, bytes):
        return func(data_or_path).hexdigest()
    
    # Otherwise treat as file path
    hasher = func()
    with open(str(data_or_path), "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    
    return hasher.hexdigest()


# =============================================================================
# TOKEN GENERATION / VERIFICATION
# =============================================================================

def generate_token(
    user_id: str,
    secret: str,
    timestamp: Optional[int] = None
) -> str:
    """
    Generate HMAC-based authentication token.
    
    Args:
        user_id: User identifier
        secret: Secret key for signing
        timestamp: Optional timestamp (default: current time)
        
    Returns:
        Token string in format "user_id:timestamp:signature"
    """
    if timestamp is None:
        timestamp = int(time.time())
    
    payload = f"{user_id}:{timestamp}"
    signature = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return f"{payload}:{signature}"


def verify_token(
    token: str,
    secret: str,
    ttl: int = 86400
) -> Optional[str]:
    """
    Verify token and return user_id if valid.
    
    Args:
        token: Token to verify
        secret: Secret key used for signing
        ttl: Token time-to-live in seconds (default: 24 hours)
        
    Returns:
        User ID if valid, None otherwise
    """
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


# =============================================================================
# ChaCha20-Poly1305 ENCRYPTION
# =============================================================================

class ChaChaEncryption:
    """
    ChaCha20-Poly1305 authenticated encryption.
    
    Requires cryptography package.
    
    Example:
        cipher = ChaChaEncryption(key_bytes)
        encrypted = cipher.encrypt(b"secret data")
        decrypted = cipher.decrypt(encrypted)
    """
    
    def __init__(self, key: bytes):
        """
        Initialize cipher.
        
        Args:
            key: 32-byte encryption key
            
        Raises:
            RuntimeError: If cryptography package not available
            ValueError: If key is not 32 bytes
        """
        if not HAS_CHACHA:
            raise RuntimeError(
                "cryptography package required. Install with: pip install cryptography"
            )
        
        if len(key) != 32:
            raise ValueError("Key must be 32 bytes")
        
        self._cipher = ChaCha20Poly1305(key)
    
    def encrypt(self, plaintext: bytes, associated_data: bytes = None) -> bytes:
        """
        Encrypt data.
        
        Args:
            plaintext: Data to encrypt
            associated_data: Optional authenticated data
            
        Returns:
            Nonce (12 bytes) + ciphertext
        """
        nonce = os.urandom(12)
        ciphertext = self._cipher.encrypt(nonce, plaintext, associated_data)
        return nonce + ciphertext
    
    def decrypt(self, data: bytes, associated_data: bytes = None) -> bytes:
        """
        Decrypt data.
        
        Args:
            data: Nonce + ciphertext
            associated_data: Optional authenticated data
            
        Returns:
            Decrypted plaintext
            
        Raises:
            ValueError: If data is too short
            cryptography.exceptions.InvalidTag: If authentication fails
        """
        if len(data) < 12:
            raise ValueError("Invalid encrypted data (too short)")
        
        nonce = data[:12]
        ciphertext = data[12:]
        return self._cipher.decrypt(nonce, ciphertext, associated_data)
    
    @classmethod
    def from_hex(cls, key_hex: str) -> "ChaChaEncryption":
        """
        Create cipher from hex-encoded key.
        
        Args:
            key_hex: 64-character hex string (32 bytes)
            
        Returns:
            ChaChaEncryption instance
        """
        key = bytes.fromhex(key_hex)
        return cls(key)
    
    @staticmethod
    def generate_key() -> bytes:
        """Generate random 32-byte key."""
        return os.urandom(32)


# =============================================================================
# PASSWORD HASHING (Argon2)
# =============================================================================

def hash_password(password: str) -> str:
    """
    Hash password using Argon2id.
    
    Args:
        password: Password to hash
        
    Returns:
        Hashed password string
        
    Raises:
        RuntimeError: If argon2-cffi not available
    """
    if not HAS_ARGON2:
        raise RuntimeError(
            "argon2-cffi package required. Install with: pip install argon2-cffi"
        )
    
    ph = PasswordHasher()
    return ph.hash(password)


def verify_password(password: str, hash_value: str) -> bool:
    """
    Verify password against Argon2 hash.
    
    Args:
        password: Password to verify
        hash_value: Stored hash
        
    Returns:
        True if password matches, False otherwise
        
    Raises:
        RuntimeError: If argon2-cffi not available
    """
    if not HAS_ARGON2:
        raise RuntimeError(
            "argon2-cffi package required. Install with: pip install argon2-cffi"
        )
    
    ph = PasswordHasher()
    try:
        ph.verify(hash_value, password)
        return True
    except VerifyMismatchError:
        return False
