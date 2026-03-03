# -*- coding: utf-8 -*-
"""Hash utilities for zsys core.

Provides hashing functions for strings and files.
"""
# RU: Утилиты хэширования строк и файлов для ядра zsys

import hashlib
from typing import Literal

__all__ = [
    "md5_hash",
    "sha256_hash",
    "sha512_hash",
    "hash_string",
    "hash_file",
    "hash_file_sync",
]

try:
    import aiofiles

    HAS_AIOFILES = True
except ImportError:
    HAS_AIOFILES = False

HashAlgorithm = Literal["md5", "sha256", "sha512", "sha1", "sha384"]


def md5_hash(text: str) -> str:
    """Calculate MD5 hash of string.

    Args:
        text: String to hash.

    Returns:
        str: MD5 hex digest.
    """
    # RU: Вычисляет MD5-хэш переданной строки
    return hashlib.md5(text.encode()).hexdigest()


def sha256_hash(text: str) -> str:
    """Calculate SHA256 hash of string.

    Args:
        text: String to hash.

    Returns:
        str: SHA256 hex digest.
    """
    # RU: Вычисляет SHA-256 хэш переданной строки
    return hashlib.sha256(text.encode()).hexdigest()


def sha512_hash(text: str) -> str:
    """Calculate SHA512 hash of string.

    Args:
        text: String to hash.

    Returns:
        str: SHA512 hex digest.
    """
    # RU: Вычисляет SHA-512 хэш переданной строки
    return hashlib.sha512(text.encode()).hexdigest()


def hash_string(text: str, algorithm: HashAlgorithm = "sha256") -> str:
    """Calculate hash of string using specified algorithm.

    Args:
        text: String to hash.
        algorithm: Hash algorithm (md5, sha256, sha512, sha1, sha384).

    Returns:
        str: Hex digest.

    Raises:
        ValueError: If algorithm is not supported.
    """
    # RU: Универсальная функция хэширования строки с выбором алгоритма
    algorithms = {
        "md5": hashlib.md5,
        "sha1": hashlib.sha1,
        "sha256": hashlib.sha256,
        "sha384": hashlib.sha384,
        "sha512": hashlib.sha512,
    }

    if algorithm not in algorithms:
        raise ValueError(f"Unsupported algorithm: {algorithm}")

    return algorithms[algorithm](text.encode()).hexdigest()


def hash_file_sync(
    file_path: str, algorithm: HashAlgorithm = "sha256", chunk_size: int = 4096
) -> str:
    """Calculate hash of file synchronously.

    Args:
        file_path: Path to file.
        algorithm: Hash algorithm.
        chunk_size: Read chunk size in bytes.

    Returns:
        str: File hash hex digest.

    Raises:
        ValueError: If algorithm is not supported.
        FileNotFoundError: If file does not exist.
    """
    # RU: Вычисляет хэш файла синхронно, читая его блоками
    algorithms = {
        "md5": hashlib.md5,
        "sha1": hashlib.sha1,
        "sha256": hashlib.sha256,
        "sha384": hashlib.sha384,
        "sha512": hashlib.sha512,
    }

    if algorithm not in algorithms:
        raise ValueError(f"Unsupported algorithm: {algorithm}")

    hash_func = algorithms[algorithm]()

    with open(file_path, "rb") as f:
        # RU: Walrus-оператор: читаем блок и проверяем его непустоту в одном выражении
        while chunk := f.read(chunk_size):
            hash_func.update(chunk)

    return hash_func.hexdigest()


async def hash_file(
    file_path: str, algorithm: HashAlgorithm = "sha256", chunk_size: int = 4096
) -> str:
    """Calculate hash of file asynchronously.

    Args:
        file_path: Path to file.
        algorithm: Hash algorithm.
        chunk_size: Read chunk size in bytes.

    Returns:
        str: File hash hex digest.

    Raises:
        ImportError: If aiofiles is not installed.
        ValueError: If algorithm is not supported.
        FileNotFoundError: If file does not exist.
    """
    # RU: Вычисляет хэш файла асинхронно с помощью aiofiles
    if not HAS_AIOFILES:
        raise ImportError("aiofiles is required for async file operations")

    algorithms = {
        "md5": hashlib.md5,
        "sha1": hashlib.sha1,
        "sha256": hashlib.sha256,
        "sha384": hashlib.sha384,
        "sha512": hashlib.sha512,
    }

    if algorithm not in algorithms:
        raise ValueError(f"Unsupported algorithm: {algorithm}")

    hash_func = algorithms[algorithm]()

    async with aiofiles.open(file_path, "rb") as f:
        # RU: Walrus-оператор в асинхронном контексте: читаем и проверяем блок атомарно
        while chunk := await f.read(chunk_size):
            hash_func.update(chunk)

    return hash_func.hexdigest()
