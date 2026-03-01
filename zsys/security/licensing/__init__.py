# -*- coding: utf-8 -*-
"""zsys core licensing - License key management system.

Provides cryptographic license key generation and validation.
"""

try:
    from .manager import (
        LicenseManager,
        hash_data,
        encrypt_data,
        decrypt_data,
        generate_license_key,
        check_license,
    )
    LICENSING_AVAILABLE = True
except ImportError:
    LICENSING_AVAILABLE = False

__all__ = [
    "LICENSING_AVAILABLE",
    "LicenseManager",
    "hash_data",
    "encrypt_data",
    "decrypt_data",
    "generate_license_key",
    "check_license",
]
