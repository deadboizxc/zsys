# -*- coding: utf-8 -*-
"""License key management for zsys core.

Provides cryptographic license key generation and validation.
Requires pycryptodome library for encryption features.
"""

import os
import base64
import hashlib
import struct
import uuid
import re
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass

# Optional crypto imports
try:
    from Crypto.PublicKey import RSA
    from Crypto.Signature import pkcs1_15
    from Crypto.Hash import SHA512, HMAC
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad, unpad
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


# Pure Python hash function (always available)
def hash_data(data: bytes) -> bytes:
    """Hash data using SHA-512.
    
    Args:
        data: Data to hash.
    
    Returns:
        Hashed data (64 bytes).
    """
    return hashlib.sha512(data).digest()


def hash_data_hex(data: bytes) -> str:
    """Hash data and return hex string.
    
    Args:
        data: Data to hash.
    
    Returns:
        Hex string of hash.
    """
    return hashlib.sha512(data).hexdigest()


# Duration parsing
def parse_duration(duration_str: str) -> timedelta:
    """Parse duration string to timedelta.
    
    Args:
        duration_str: Duration string (e.g., "1y", "2m", "30d").
    
    Returns:
        timedelta object.
    
    Example:
        parse_duration("1y2m30d")  # 1 year, 2 months, 30 days
    """
    pattern = re.compile(r'(\d+)([ymd])')
    matches = pattern.findall(duration_str.lower())
    duration = timedelta(days=0)
    
    for value, unit in matches:
        value = int(value)
        if unit == 'y':
            duration += timedelta(days=value * 365)
        elif unit == 'm':
            duration += timedelta(days=value * 30)
        elif unit == 'd':
            duration += timedelta(days=value)
    
    return duration


def calculate_expiration(duration_str: str) -> int:
    """Calculate expiration timestamp from duration string.
    
    Args:
        duration_str: Duration string (e.g., "1y", "30d").
    
    Returns:
        Expiration timestamp.
    """
    duration = parse_duration(duration_str)
    return int((datetime.now() + duration).timestamp())


@dataclass
class LicenseData:
    """License key data structure."""
    user_id: str
    uuid: bytes
    expiration: int
    created: int
    hash: bytes
    
    @property
    def is_expired(self) -> bool:
        """Check if license is expired."""
        return datetime.now().timestamp() > self.expiration
    
    @property
    def days_remaining(self) -> int:
        """Get days remaining until expiration."""
        remaining = self.expiration - datetime.now().timestamp()
        return max(0, int(remaining / 86400))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "user_id": self.user_id,
            "uuid": base64.b64encode(self.uuid).decode(),
            "expiration": self.expiration,
            "created": self.created,
            "is_expired": self.is_expired,
            "days_remaining": self.days_remaining
        }


class LicenseManager:
    """License key manager with encryption support.
    
    Example:
        manager = LicenseManager(main_key=b"secret_key_512_bytes...")
        license_key = manager.generate("user123", "1y")
        is_valid, data = manager.validate(license_key, "user123")
    """
    
    def __init__(self, main_key: Optional[bytes] = None):
        """Initialize license manager.
        
        Args:
            main_key: 512-byte main key for license generation.
        """
        if not CRYPTO_AVAILABLE:
            raise ImportError(
                "pycryptodome is required for LicenseManager. "
                "Install with: pip install pycryptodome"
            )
        
        self.main_key = main_key or os.urandom(512)
        self._aes_key = hashlib.sha256(self.main_key).digest()  # 32 bytes for AES
    
    def generate(self, user_id: str, duration: str) -> bytes:
        """Generate a license key.
        
        Args:
            user_id: User identifier.
            duration: Duration string (e.g., "1y", "30d").
        
        Returns:
            License key bytes.
        """
        expiration = calculate_expiration(duration)
        created = int(datetime.now().timestamp())
        license_uuid = uuid.uuid4().bytes
        
        # Create license data
        license_data = (
            user_id.encode('utf-8') +
            self.main_key +
            license_uuid +
            struct.pack('II', expiration, created)
        )
        
        # Hash the data
        license_hash = hash_data(license_data)
        
        # Create final key structure
        key_structure = (
            struct.pack('H', len(user_id)) +  # user_id length
            user_id.encode('utf-8') +
            license_uuid +
            struct.pack('II', expiration, created) +
            license_hash
        )
        
        # Encrypt
        return self._encrypt(key_structure)
    
    def validate(
        self, 
        license_key: bytes, 
        user_id: str
    ) -> Tuple[bool, Optional[LicenseData]]:
        """Validate a license key.
        
        Args:
            license_key: Encrypted license key.
            user_id: Expected user ID.
        
        Returns:
            Tuple of (is_valid, LicenseData or None).
        """
        try:
            # Decrypt
            decrypted = self._decrypt(license_key)
            
            # Parse structure
            user_id_len = struct.unpack('H', decrypted[:2])[0]
            offset = 2
            
            stored_user_id = decrypted[offset:offset + user_id_len].decode('utf-8')
            offset += user_id_len
            
            license_uuid = decrypted[offset:offset + 16]
            offset += 16
            
            expiration, created = struct.unpack('II', decrypted[offset:offset + 8])
            offset += 8
            
            stored_hash = decrypted[offset:offset + 64]
            
            # Verify user_id
            if stored_user_id != user_id:
                return False, None
            
            # Recreate and verify hash
            license_data = (
                user_id.encode('utf-8') +
                self.main_key +
                license_uuid +
                struct.pack('II', expiration, created)
            )
            
            expected_hash = hash_data(license_data)
            if stored_hash != expected_hash:
                return False, None
            
            # Create license data object
            data = LicenseData(
                user_id=user_id,
                uuid=license_uuid,
                expiration=expiration,
                created=created,
                hash=stored_hash
            )
            
            # Check expiration
            if data.is_expired:
                return False, data
            
            return True, data
            
        except Exception:
            return False, None
    
    def _encrypt(self, data: bytes) -> bytes:
        """Encrypt data with AES.
        
        Args:
            data: Data to encrypt.
        
        Returns:
            Encrypted data with IV prepended.
        """
        cipher = AES.new(self._aes_key, AES.MODE_CBC)
        ct_bytes = cipher.encrypt(pad(data, AES.block_size))
        return cipher.iv + ct_bytes
    
    def _decrypt(self, encrypted_data: bytes) -> bytes:
        """Decrypt AES encrypted data.
        
        Args:
            encrypted_data: Encrypted data with IV prepended.
        
        Returns:
            Decrypted data.
        """
        iv = encrypted_data[:AES.block_size]
        ct = encrypted_data[AES.block_size:]
        cipher = AES.new(self._aes_key, AES.MODE_CBC, iv)
        return unpad(cipher.decrypt(ct), AES.block_size)
    
    def to_base64(self, license_key: bytes) -> str:
        """Convert license key to base64 string.
        
        Args:
            license_key: License key bytes.
        
        Returns:
            Base64 encoded string.
        """
        return base64.b64encode(license_key).decode('utf-8')
    
    def from_base64(self, license_str: str) -> bytes:
        """Convert base64 string to license key.
        
        Args:
            license_str: Base64 encoded string.
        
        Returns:
            License key bytes.
        """
        return base64.b64decode(license_str.encode('utf-8'))
    
    @classmethod
    def generate_main_key(cls, path: Optional[str] = None) -> bytes:
        """Generate a new 512-byte main key.
        
        Args:
            path: Optional path to save the key.
        
        Returns:
            Generated key bytes.
        """
        key = os.urandom(512)
        
        if path:
            with open(path, 'wb') as f:
                f.write(key)
        
        return key
    
    @classmethod
    def load_main_key(cls, path: str) -> bytes:
        """Load main key from file.
        
        Args:
            path: Path to key file.
        
        Returns:
            Key bytes.
        """
        with open(path, 'rb') as f:
            return f.read()


# Simplified functions for basic usage
def generate_license_key(
    main_key: bytes,
    user_id: str,
    duration: str
) -> bytes:
    """Generate a license key (simplified).
    
    Args:
        main_key: 512-byte main key.
        user_id: User identifier.
        duration: Duration string.
    
    Returns:
        License key bytes.
    """
    manager = LicenseManager(main_key)
    return manager.generate(user_id, duration)


def check_license(
    main_key: bytes,
    license_key: bytes,
    user_id: str
) -> Tuple[bool, Optional[LicenseData]]:
    """Validate a license key (simplified).
    
    Args:
        main_key: 512-byte main key.
        license_key: License key bytes.
        user_id: User identifier.
    
    Returns:
        Tuple of (is_valid, LicenseData or None).
    """
    manager = LicenseManager(main_key)
    return manager.validate(license_key, user_id)


# For convenience without crypto
def encrypt_data(data: bytes, key: bytes) -> bytes:
    """Encrypt data with AES (requires pycryptodome).
    
    Args:
        data: Data to encrypt.
        key: Encryption key (will be hashed to 32 bytes).
    
    Returns:
        Encrypted data.
    """
    if not CRYPTO_AVAILABLE:
        raise ImportError("pycryptodome required for encryption")
    
    aes_key = hashlib.sha256(key).digest()
    cipher = AES.new(aes_key, AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(data, AES.block_size))
    return cipher.iv + ct_bytes


def decrypt_data(encrypted_data: bytes, key: bytes) -> bytes:
    """Decrypt AES encrypted data (requires pycryptodome).
    
    Args:
        encrypted_data: Encrypted data.
        key: Encryption key.
    
    Returns:
        Decrypted data.
    """
    if not CRYPTO_AVAILABLE:
        raise ImportError("pycryptodome required for decryption")
    
    aes_key = hashlib.sha256(key).digest()
    iv = encrypted_data[:AES.block_size]
    ct = encrypted_data[AES.block_size:]
    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(ct), AES.block_size)
