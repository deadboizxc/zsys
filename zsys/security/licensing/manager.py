"""License manager — AES-CBC encrypted license keys with expiry and user binding.

Provides LicenseManager class and standalone helper functions for generating
and validating cryptographic license keys. Keys are AES-CBC encrypted blobs
containing user_id, UUID, creation/expiration timestamps, and SHA-512 hash.
Requires: pip install pycryptodome.
"""
# RU: Менеджер лицензий — зашифрованные AES-CBC лицензионные ключи с привязкой к пользователю.
# RU: Требует: pip install pycryptodome.

import base64
import hashlib
import os
import re
import struct
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

# Optional crypto imports
try:
    from Crypto.Cipher import AES
    from Crypto.Hash import HMAC, SHA512
    from Crypto.PublicKey import RSA
    from Crypto.Signature import pkcs1_15
    from Crypto.Util.Padding import pad, unpad

    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


# Pure Python hash function (always available)
def hash_data(data: bytes) -> bytes:
    """Compute the SHA-512 binary digest of *data*.

    Args:
        data: Bytes to hash.

    Returns:
        64-byte SHA-512 binary digest.
    """
    # RU: SHA-512 бинарный дайджест.
    return hashlib.sha512(data).digest()


def hash_data_hex(data: bytes) -> str:
    """Compute the SHA-512 hexadecimal digest of *data*.

    Args:
        data: Bytes to hash.

    Returns:
        128-character lowercase hexadecimal SHA-512 digest string.
    """
    # RU: SHA-512 hex-дайджест.
    return hashlib.sha512(data).hexdigest()


# Duration parsing
def parse_duration(duration_str: str) -> timedelta:
    """Parse a compact duration string into a :class:`timedelta`.

    Uses a regex to find ``(value, unit)`` pairs where unit is one of
    ``y`` (year = 365 days), ``m`` (month = 30 days), or ``d`` (day).
    Multiple units may be combined, e.g. ``"1y2m30d"``.

    Args:
        duration_str: Duration string such as ``"1y"``, ``"30d"``, or
            ``"1y2m30d"``.

    Returns:
        :class:`datetime.timedelta` representing the total duration.

    Example:
        parse_duration("1y2m30d")  # 1 year, 2 months, 30 days
    """
    # RU: Regex ищет пары (число, единица); y=365d, m=30d; суммирует timedelta.
    pattern = re.compile(r"(\d+)([ymd])")
    matches = pattern.findall(duration_str.lower())
    duration = timedelta(days=0)

    for value, unit in matches:
        value = int(value)
        if unit == "y":
            duration += timedelta(days=value * 365)
        elif unit == "m":
            duration += timedelta(days=value * 30)
        elif unit == "d":
            duration += timedelta(days=value)

    return duration


def calculate_expiration(duration_str: str) -> int:
    """Calculate the Unix timestamp at which a license will expire.

    Args:
        duration_str: Duration string such as ``"1y"`` or ``"30d"``.

    Returns:
        Integer Unix timestamp for the expiration moment.
    """
    # RU: parse_duration + datetime.now() → Unix-timestamp.
    duration = parse_duration(duration_str)
    return int((datetime.now() + duration).timestamp())


@dataclass
class LicenseData:
    """Parsed license key data returned by :meth:`LicenseManager.validate`.

    Attributes:
        user_id: User identifier embedded in the license.
        uuid: 16-byte UUID bytes uniquely identifying this license.
        expiration: Unix timestamp after which the license is invalid.
        created: Unix timestamp when the license was generated.
        hash: 64-byte SHA-512 hash used to verify key integrity.
    """

    # RU: Данные лицензии; свойства is_expired, days_remaining и to_dict.
    user_id: str
    uuid: bytes
    expiration: int
    created: int
    hash: bytes

    @property
    def is_expired(self) -> bool:
        """Return ``True`` if the license expiration timestamp is in the past.

        Returns:
            ``True`` when the current UTC time exceeds *expiration*.
        """
        # RU: True если текущее время > expiration.
        return datetime.now().timestamp() > self.expiration

    @property
    def days_remaining(self) -> int:
        """Return the number of whole days until the license expires.

        Returns:
            Non-negative integer; ``0`` when the license is already expired.
        """
        # RU: Целое число дней до истечения; 0 если уже просрочена.
        remaining = self.expiration - datetime.now().timestamp()
        return max(0, int(remaining / 86400))

    def to_dict(self) -> Dict[str, Any]:
        """Serialize this instance to a plain dictionary.

        Returns:
            Dictionary with keys ``user_id``, ``uuid`` (Base64 string),
            ``expiration``, ``created``, ``is_expired``, and
            ``days_remaining``.
        """
        # RU: Сериализует в словарь; UUID кодируется в Base64.
        return {
            "user_id": self.user_id,
            "uuid": base64.b64encode(self.uuid).decode(),
            "expiration": self.expiration,
            "created": self.created,
            "is_expired": self.is_expired,
            "days_remaining": self.days_remaining,
        }


class LicenseManager:
    """AES-CBC encrypted license key manager with user binding and expiry.

    Attributes:
        main_key: 512-byte master key used to derive the AES encryption key
            and to compute the integrity hash.
        _aes_key: 32-byte AES key derived from *main_key* via SHA-256.
    """

    # RU: AES-CBC лицензионные ключи; _aes_key = SHA-256(main_key).

    def __init__(self, main_key: Optional[bytes] = None):
        """Initialise the manager and derive the 32-byte AES key.

        Args:
            main_key: 512-byte master key for license generation and
                validation.  A random 512-byte key is generated when
                ``None`` is passed.

        Raises:
            ImportError: When ``pycryptodome`` is not installed.
        """
        # RU: SHA-256(main_key) → 32-байтный AES-ключ; ImportError если pycryptodome отсутствует.
        if not CRYPTO_AVAILABLE:
            raise ImportError(
                "pycryptodome is required for LicenseManager. "
                "Install with: pip install pycryptodome"
            )

        self.main_key = main_key or os.urandom(512)
        self._aes_key = hashlib.sha256(self.main_key).digest()  # 32 bytes for AES

    def generate(self, user_id: str, duration: str) -> bytes:
        """Build and encrypt a license key blob.

        Assembles a key structure with ``struct.pack``: a 2-byte
        user-id length header, the UTF-8 user ID, a 16-byte UUID, two
        packed 32-bit timestamps (expiration + created), and a 64-byte
        SHA-512 integrity hash.  The structure is AES-CBC encrypted.

        Args:
            user_id: User identifier to bind to the license.
            duration: Duration string, e.g. ``"1y"`` or ``"30d"``.

        Returns:
            AES-CBC encrypted license key bytes (IV prepended).
        """
        # RU: struct.pack → key_structure → AES-CBC encrypt; возвращает зашифрованный blob.
        expiration = calculate_expiration(duration)
        created = int(datetime.now().timestamp())
        license_uuid = uuid.uuid4().bytes

        # Create license data
        license_data = (
            user_id.encode("utf-8")
            + self.main_key
            + license_uuid
            + struct.pack("II", expiration, created)
        )

        # Hash the data
        license_hash = hash_data(license_data)

        # Create final key structure
        key_structure = (
            struct.pack("H", len(user_id))  # user_id length
            + user_id.encode("utf-8")
            + license_uuid
            + struct.pack("II", expiration, created)
            + license_hash
        )

        # Encrypt
        return self._encrypt(key_structure)

    def validate(
        self, license_key: bytes, user_id: str
    ) -> Tuple[bool, Optional[LicenseData]]:
        """Decrypt and validate a license key.

        Decrypts the blob, parses the user-id-length header to extract
        *user_id*, then re-derives and compares the SHA-512 integrity hash.
        Finally checks whether the license has expired.

        Args:
            license_key: Encrypted license key bytes as returned by
                :meth:`generate`.
            user_id: Expected user identifier.

        Returns:
            Tuple of ``(is_valid, LicenseData | None)``.  Returns
            ``(False, LicenseData)`` when the key is valid but expired.
            Returns ``(False, None)`` on parse or integrity errors.
        """
        # RU: Дешифрует; разбирает user_id_len заголовок; проверяет user_id, hash, срок действия.
        try:
            # Decrypt
            decrypted = self._decrypt(license_key)

            # Parse structure
            user_id_len = struct.unpack("H", decrypted[:2])[0]
            offset = 2

            stored_user_id = decrypted[offset : offset + user_id_len].decode("utf-8")
            offset += user_id_len

            license_uuid = decrypted[offset : offset + 16]
            offset += 16

            expiration, created = struct.unpack("II", decrypted[offset : offset + 8])
            offset += 8

            stored_hash = decrypted[offset : offset + 64]

            # Verify user_id
            if stored_user_id != user_id:
                return False, None

            # Recreate and verify hash
            license_data = (
                user_id.encode("utf-8")
                + self.main_key
                + license_uuid
                + struct.pack("II", expiration, created)
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
                hash=stored_hash,
            )

            # Check expiration
            if data.is_expired:
                return False, data

            return True, data

        except Exception:
            return False, None

    def _encrypt(self, data: bytes) -> bytes:
        """Encrypt *data* with AES-CBC and a random IV.

        Args:
            data: Plaintext bytes to encrypt.

        Returns:
            Random IV (``AES.block_size`` bytes) prepended to the PKCS7-padded
            ciphertext.
        """
        # RU: AES-CBC; случайный IV предваряет шифртекст.
        cipher = AES.new(self._aes_key, AES.MODE_CBC)
        ct_bytes = cipher.encrypt(pad(data, AES.block_size))
        return cipher.iv + ct_bytes

    def _decrypt(self, encrypted_data: bytes) -> bytes:
        """Decrypt an AES-CBC blob produced by :meth:`_encrypt`.

        Args:
            encrypted_data: IV (first ``AES.block_size`` bytes) followed by
                the PKCS7-padded ciphertext.

        Returns:
            Decrypted plaintext bytes with padding removed.
        """
        # RU: Извлекает IV из первых block_size байт; AES-CBC decrypt + unpad.
        iv = encrypted_data[: AES.block_size]
        ct = encrypted_data[AES.block_size :]
        cipher = AES.new(self._aes_key, AES.MODE_CBC, iv)
        return unpad(cipher.decrypt(ct), AES.block_size)

    def to_base64(self, license_key: bytes) -> str:
        """Base64-encode a license key for safe text transport.

        Args:
            license_key: Raw license key bytes.

        Returns:
            Base64-encoded string (standard alphabet, no line breaks).
        """
        # RU: base64.b64encode → UTF-8 строка.
        return base64.b64encode(license_key).decode("utf-8")

    def from_base64(self, license_str: str) -> bytes:
        """Decode a Base64-encoded license key back to raw bytes.

        Args:
            license_str: Base64-encoded string as returned by
                :meth:`to_base64`.

        Returns:
            Raw license key bytes.
        """
        # RU: base64.b64decode → bytes.
        return base64.b64decode(license_str.encode("utf-8"))

    @classmethod
    def generate_main_key(cls, path: Optional[str] = None) -> bytes:
        """Generate a new 512-byte random master key and optionally save it.

        Args:
            path: File path to write the key to in binary mode.  When
                ``None`` the key is only returned and not persisted.

        Returns:
            512 random bytes of key material.
        """
        # RU: os.urandom(512); если path задан — сохраняет в файл.
        key = os.urandom(512)

        if path:
            with open(path, "wb") as f:
                f.write(key)

        return key

    @classmethod
    def load_main_key(cls, path: str) -> bytes:
        """Load the master key from a binary file.

        Args:
            path: Path to the binary key file created by
                :meth:`generate_main_key`.

        Returns:
            Raw key bytes read from the file.
        """
        # RU: Читает бинарный файл и возвращает байты ключа.
        with open(path, "rb") as f:
            return f.read()


# Simplified functions for basic usage
def generate_license_key(main_key: bytes, user_id: str, duration: str) -> bytes:
    """Simplified wrapper around :meth:`LicenseManager.generate`.

    Args:
        main_key: 512-byte master key.
        user_id: User identifier to bind to the license.
        duration: Duration string, e.g. ``"1y"`` or ``"30d"``.

    Returns:
        AES-CBC encrypted license key bytes.
    """
    # RU: Создаёт LicenseManager и вызывает generate(user_id, duration).
    manager = LicenseManager(main_key)
    return manager.generate(user_id, duration)


def check_license(
    main_key: bytes, license_key: bytes, user_id: str
) -> Tuple[bool, Optional[LicenseData]]:
    """Simplified wrapper around :meth:`LicenseManager.validate`.

    Args:
        main_key: 512-byte master key matching the one used to generate the
            license.
        license_key: Encrypted license key bytes.
        user_id: Expected user identifier.

    Returns:
        Tuple of ``(is_valid, LicenseData | None)``.
    """
    # RU: Создаёт LicenseManager и вызывает validate(license_key, user_id).
    manager = LicenseManager(main_key)
    return manager.validate(license_key, user_id)


# For convenience without crypto
def encrypt_data(data: bytes, key: bytes) -> bytes:
    """Encrypt *data* with AES-CBC, hashing *key* to 32 bytes first.

    Standalone helper that does not require a :class:`LicenseManager`
    instance.  The raw *key* is passed through SHA-256 to produce the
    32-byte AES key.

    Args:
        data: Plaintext bytes to encrypt.
        key: Arbitrary-length key bytes; hashed to 32 bytes via SHA-256.

    Returns:
        Random IV (``AES.block_size`` bytes) prepended to the ciphertext.

    Raises:
        ImportError: When ``pycryptodome`` is not installed.
    """
    # RU: SHA-256(key) → 32-байтный AES-ключ; AES-CBC encrypt.
    if not CRYPTO_AVAILABLE:
        raise ImportError("pycryptodome required for encryption")

    aes_key = hashlib.sha256(key).digest()
    cipher = AES.new(aes_key, AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(data, AES.block_size))
    return cipher.iv + ct_bytes


def decrypt_data(encrypted_data: bytes, key: bytes) -> bytes:
    """Decrypt an AES-CBC blob produced by :func:`encrypt_data`.

    The raw *key* is hashed to 32 bytes via SHA-256 before decryption.

    Args:
        encrypted_data: IV (first ``AES.block_size`` bytes) followed by
            the ciphertext.
        key: Arbitrary-length key bytes matching those used during encryption.

    Returns:
        Decrypted plaintext bytes with PKCS7 padding removed.

    Raises:
        ImportError: When ``pycryptodome`` is not installed.
    """
    # RU: SHA-256(key) → 32-байтный AES-ключ; AES-CBC decrypt.
    if not CRYPTO_AVAILABLE:
        raise ImportError("pycryptodome required for decryption")

    aes_key = hashlib.sha256(key).digest()
    iv = encrypted_data[: AES.block_size]
    ct = encrypted_data[AES.block_size :]
    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(ct), AES.block_size)
