# -*- coding: utf-8 -*-
"""Licensing package — cryptographic license key generation and validation.

Wraps LicenseManager and helper functions from the manager module.
Sets LICENSING_AVAILABLE=False when pycryptodome is not installed,
allowing graceful feature degradation.
"""
# RU: Пакет лицензирования — генерация и проверка лицензионных ключей.
# RU: LICENSING_AVAILABLE=False если pycryptodome не установлен.

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
