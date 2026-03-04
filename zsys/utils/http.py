# -*- coding: utf-8 -*-
"""HTTP utilities for zsys core.

Provides async HTTP request functions.
"""
# RU: Асинхронные HTTP-утилиты — загрузка данных, JSON-запросы и скачивание файлов.

from typing import Any, Dict, Optional

__all__ = [
    "fetch_url",
    "fetch_json",
    "fetch_status",
    "download_file",
    "post_json",
]

try:
    import aiohttp

    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

try:
    import aiofiles

    HAS_AIOFILES = True
except ImportError:
    HAS_AIOFILES = False


async def fetch_url(
    url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 30
) -> str:
    """Fetch URL content as text.

    Args:
        url: URL to fetch.
        headers: Optional request headers.
        timeout: Request timeout in seconds.

    Returns:
        str: Response text.

    Raises:
        ImportError: If aiohttp is not installed.
    """
    # RU: Открывает сессию aiohttp, выполняет GET-запрос и возвращает тело ответа как строку.
    if not HAS_AIOHTTP:
        raise ImportError("aiohttp is required for HTTP operations")

    async with aiohttp.ClientSession() as session:
        async with session.get(
            url, headers=headers, timeout=aiohttp.ClientTimeout(total=timeout)
        ) as response:
            return await response.text()


async def fetch_json(
    url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 30
) -> Dict[str, Any]:
    """Fetch URL content as JSON.

    Args:
        url: URL to fetch.
        headers: Optional request headers.
        timeout: Request timeout in seconds.

    Returns:
        dict: Response JSON.

    Raises:
        ImportError: If aiohttp is not installed.
    """
    # RU: Выполняет GET-запрос и десериализует JSON-ответ через aiohttp.
    if not HAS_AIOHTTP:
        raise ImportError("aiohttp is required for HTTP operations")

    async with aiohttp.ClientSession() as session:
        async with session.get(
            url, headers=headers, timeout=aiohttp.ClientTimeout(total=timeout)
        ) as response:
            return await response.json()


async def fetch_status(url: str, timeout: int = 30) -> int:
    """Get HTTP status code for URL.

    Args:
        url: URL to check.
        timeout: Request timeout in seconds.

    Returns:
        int: HTTP status code.

    Raises:
        ImportError: If aiohttp is not installed.
    """
    # RU: Выполняет HEAD-like GET запрос и возвращает HTTP-статус без чтения тела ответа.
    if not HAS_AIOHTTP:
        raise ImportError("aiohttp is required for HTTP operations")

    async with aiohttp.ClientSession() as session:
        async with session.get(
            url, timeout=aiohttp.ClientTimeout(total=timeout)
        ) as response:
            return response.status


async def download_file(
    url: str,
    path: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 300,
    chunk_size: int = 8192,
) -> str:
    """Download file from URL.

    Args:
        url: URL to download.
        path: Local file path to save to.
        headers: Optional request headers.
        timeout: Request timeout in seconds.
        chunk_size: Download chunk size in bytes.

    Returns:
        str: Path to downloaded file.

    Raises:
        ImportError: If aiohttp or aiofiles is not installed.
    """
    # RU: Скачивает файл потоковой передачей — записывает чанки асинхронно, не загружая всё в память.
    if not HAS_AIOHTTP:
        raise ImportError("aiohttp is required for HTTP operations")
    if not HAS_AIOFILES:
        raise ImportError("aiofiles is required for async file operations")

    async with aiohttp.ClientSession() as session:
        async with session.get(
            url, headers=headers, timeout=aiohttp.ClientTimeout(total=timeout)
        ) as response:
            async with aiofiles.open(path, "wb") as f:
                async for chunk in response.content.iter_chunked(
                    chunk_size
                ):  # RU: iter_chunked позволяет читать ответ частями без буферизации всего тела
                    await f.write(chunk)

    return path


async def post_json(
    url: str,
    data: Dict[str, Any],
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 30,
) -> Dict[str, Any]:
    """POST JSON data and return JSON response.

    Args:
        url: URL to post to.
        data: JSON data to send.
        headers: Optional request headers.
        timeout: Request timeout in seconds.

    Returns:
        dict: Response JSON.

    Raises:
        ImportError: If aiohttp is not installed.
    """
    # RU: Отправляет POST-запрос с JSON-телом и десериализует JSON-ответ.
    if not HAS_AIOHTTP:
        raise ImportError("aiohttp is required for HTTP operations")

    async with aiohttp.ClientSession() as session:
        async with session.post(
            url,
            json=data,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=timeout),
        ) as response:
            return await response.json()
