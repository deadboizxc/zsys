"""
Base HTTP client interface.

All HTTP clients should inherit from BaseHttpClient.
Provides abstract interface for HTTP operations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseHttpClient(ABC):
    """
    Abstract base HTTP client.

    All HTTP transport implementations must inherit from this.
    Provides unified interface for HTTP operations.

    Example:
        class MyHttpClient(BaseHttpClient):
            async def get(self, path, **kwargs):
                # implementation
                pass
    """

    def __init__(
        self,
        base_url: str = "",
        timeout: float = 30.0,
        headers: Optional[Dict[str, str]] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.headers = headers or {}
        self._session = None

    @abstractmethod
    async def __aenter__(self) -> "BaseHttpClient":
        """Enter async context."""
        pass

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context."""
        pass

    @abstractmethod
    async def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Any:
        """
        Make GET request.

        Args:
            path: URL path (appended to base_url)
            params: Query parameters
            headers: Additional headers
            **kwargs: Additional options

        Returns:
            Response object
        """
        pass

    @abstractmethod
    async def post(
        self,
        path: str,
        data: Optional[Any] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Any:
        """
        Make POST request.

        Args:
            path: URL path
            data: Form data
            json: JSON body
            headers: Additional headers

        Returns:
            Response object
        """
        pass

    @abstractmethod
    async def put(
        self,
        path: str,
        data: Optional[Any] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Any:
        """Make PUT request."""
        pass

    @abstractmethod
    async def delete(
        self, path: str, headers: Optional[Dict[str, str]] = None, **kwargs
    ) -> Any:
        """Make DELETE request."""
        pass

    @abstractmethod
    async def patch(
        self,
        path: str,
        data: Optional[Any] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Any:
        """Make PATCH request."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the HTTP session."""
        pass

    # Convenience methods with default implementations

    async def get_json(
        self, path: str, params: Optional[Dict[str, Any]] = None, **kwargs
    ) -> Any:
        """GET request returning JSON."""
        response = await self.get(path, params=params, **kwargs)
        return await self._extract_json(response)

    async def post_json(
        self, path: str, json: Optional[Dict[str, Any]] = None, **kwargs
    ) -> Any:
        """POST request returning JSON."""
        response = await self.post(path, json=json, **kwargs)
        return await self._extract_json(response)

    @abstractmethod
    async def _extract_json(self, response: Any) -> Any:
        """Extract JSON from response object."""
        pass

    def _build_url(self, path: str) -> str:
        """Build full URL from base_url and path."""
        if path.startswith(("http://", "https://")):
            return path
        return f"{self.base_url}/{path.lstrip('/')}"

    def _merge_headers(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Merge default headers with extra headers."""
        result = dict(self.headers)
        if extra:
            result.update(extra)
        return result


__all__ = ["BaseHttpClient"]
