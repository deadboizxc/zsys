"""
Async HTTP client with aiohttp/httpx support.

Inherits from BaseHttpClient and implements unified HTTP interface.
"""

import asyncio
from typing import Any, Dict, Optional, Union
from pathlib import Path

from .base import BaseHttpClient


# Detect available HTTP library
AIOHTTP_AVAILABLE = False
HTTPX_AVAILABLE = False

try:
    import aiohttp

    AIOHTTP_AVAILABLE = True
except ImportError:
    pass

try:
    import httpx

    HTTPX_AVAILABLE = True
except ImportError:
    pass


class RetryConfig:
    """Configuration for request retries."""

    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        backoff_factor: float = 2.0,
        retry_statuses: tuple = (500, 502, 503, 504),
    ):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.backoff_factor = backoff_factor
        self.retry_statuses = retry_statuses


class HttpClient(BaseHttpClient):
    """
    Unified async HTTP client.

    Uses aiohttp if available, otherwise httpx.
    Inherits from BaseHttpClient for consistent interface.

    Example:
        async with HttpClient(base_url="https://api.example.com") as client:
            data = await client.get_json("/users")
            result = await client.post_json("/users", json={"name": "John"})
    """

    def __init__(
        self,
        base_url: str = "",
        timeout: float = 30.0,
        headers: Optional[Dict[str, str]] = None,
        retry_config: Optional[RetryConfig] = None,
    ):
        super().__init__(base_url=base_url, timeout=timeout, headers=headers)
        self.retry_config = retry_config

        self._client_type = (
            "aiohttp" if AIOHTTP_AVAILABLE else "httpx" if HTTPX_AVAILABLE else None
        )

        if self._client_type is None:
            raise ImportError(
                "Neither aiohttp nor httpx is installed. "
                "Install: pip install aiohttp or pip install httpx"
            )

    async def __aenter__(self) -> "HttpClient":
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def _ensure_session(self) -> None:
        """Create session if not exists."""
        if self._session is not None:
            return

        if self._client_type == "aiohttp":
            timeout_obj = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(
                timeout=timeout_obj, headers=self.headers
            )
        else:
            self._session = httpx.AsyncClient(
                timeout=self.timeout, headers=self.headers
            )

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session is not None:
            await self._session.close()
            self._session = None

    async def request(self, method: str, path: str, **kwargs) -> Any:
        """
        Execute HTTP request with optional retry.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            path: URL path
            **kwargs: Additional parameters (json, data, params, headers)

        Returns:
            Response object
        """
        await self._ensure_session()
        url = self._build_url(path)

        if self.retry_config:
            return await self._request_with_retry(method, url, **kwargs)

        return await self._do_request(method, url, **kwargs)

    async def _request_with_retry(self, method: str, url: str, **kwargs) -> Any:
        """Execute request with retry logic."""
        config = self.retry_config
        last_error = None

        for attempt in range(config.max_retries + 1):
            try:
                response = await self._do_request(method, url, **kwargs)

                # Check if needs retry
                status = (
                    response.status
                    if self._client_type == "aiohttp"
                    else response.status_code
                )
                if status in config.retry_statuses and attempt < config.max_retries:
                    delay = config.retry_delay * (config.backoff_factor**attempt)
                    await asyncio.sleep(delay)
                    continue

                return response

            except Exception as e:
                last_error = e
                if attempt < config.max_retries:
                    delay = config.retry_delay * (config.backoff_factor**attempt)
                    await asyncio.sleep(delay)
                    continue
                raise

        raise last_error

    async def _do_request(self, method: str, url: str, **kwargs) -> Any:
        """Execute request without retry."""
        if self._client_type == "aiohttp":
            return await self._session.request(method, url, **kwargs)
        else:
            return await self._session.request(method, url, **kwargs)

    async def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Any:
        """Make GET request."""
        if params:
            kwargs["params"] = params
        if headers:
            kwargs["headers"] = self._merge_headers(headers)
        return await self.request("GET", path, **kwargs)

    async def post(
        self,
        path: str,
        data: Optional[Any] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Any:
        """Make POST request."""
        if data:
            kwargs["data"] = data
        if json:
            kwargs["json"] = json
        if headers:
            kwargs["headers"] = self._merge_headers(headers)
        return await self.request("POST", path, **kwargs)

    async def put(
        self,
        path: str,
        data: Optional[Any] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Any:
        """Make PUT request."""
        if data:
            kwargs["data"] = data
        if json:
            kwargs["json"] = json
        if headers:
            kwargs["headers"] = self._merge_headers(headers)
        return await self.request("PUT", path, **kwargs)

    async def delete(
        self, path: str, headers: Optional[Dict[str, str]] = None, **kwargs
    ) -> Any:
        """Make DELETE request."""
        if headers:
            kwargs["headers"] = self._merge_headers(headers)
        return await self.request("DELETE", path, **kwargs)

    async def patch(
        self,
        path: str,
        data: Optional[Any] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Any:
        """Make PATCH request."""
        if data:
            kwargs["data"] = data
        if json:
            kwargs["json"] = json
        if headers:
            kwargs["headers"] = self._merge_headers(headers)
        return await self.request("PATCH", path, **kwargs)

    async def _extract_json(self, response: Any) -> Any:
        """Extract JSON from response."""
        if self._client_type == "aiohttp":
            return await response.json()
        else:
            return response.json()

    async def get_text(self, path: str, **kwargs) -> str:
        """GET request returning text."""
        response = await self.get(path, **kwargs)
        if self._client_type == "aiohttp":
            return await response.text()
        else:
            return response.text

    async def get_bytes(self, path: str, **kwargs) -> bytes:
        """GET request returning bytes."""
        response = await self.get(path, **kwargs)
        if self._client_type == "aiohttp":
            return await response.read()
        else:
            return response.content

    async def download(
        self, path: str, dest: Union[str, Path], chunk_size: int = 8192, **kwargs
    ) -> Path:
        """
        Download file.

        Args:
            path: URL path
            dest: Destination path
            chunk_size: Chunk size for streaming
            **kwargs: Additional request parameters

        Returns:
            Path to downloaded file
        """
        dest_path = Path(dest)
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        response = await self.get(path, **kwargs)

        with open(dest_path, "wb") as f:
            if self._client_type == "aiohttp":
                async for chunk in response.content.iter_chunked(chunk_size):
                    f.write(chunk)
            else:
                async for chunk in response.aiter_bytes(chunk_size):
                    f.write(chunk)

        return dest_path


async def request(url: str, method: str = "GET", **kwargs) -> Any:
    """
    Simple function for HTTP request.

    Args:
        url: Request URL
        method: HTTP method
        **kwargs: Parameters for HttpClient

    Returns:
        Response object
    """
    async with HttpClient() as client:
        return await client.request(method, url, **kwargs)


__all__ = [
    "HttpClient",
    "BaseHttpClient",
    "RetryConfig",
    "request",
    "AIOHTTP_AVAILABLE",
    "HTTPX_AVAILABLE",
]
