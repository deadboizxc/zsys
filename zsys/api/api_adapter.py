"""
API Adapter - связующий слой между core и API infra.

Provides unified interface for working with different API frameworks
(FastAPI, Flask, Aiohttp) through core interfaces.

Usage:
    from zsys.api.adapters import APIAdapter

    # Create adapter
    adapter = APIAdapter(
        backend='fastapi',
        host='0.0.0.0',
        port=8000
    )

    # Get API server implementing IAPIServer interface
    api = adapter.get_server()
    await api.start()
"""

from typing import Optional, Literal, Any
from zsys.core.interfaces import IAPIServer
from zsys.core.exceptions import APIError

Backend = Literal["fastapi", "flask", "aiohttp"]


class APIAdapter:
    """
    Adapter for creating API servers through unified interface.

    Hides backend selection complexity and provides IAPIServer interface.
    """

    def __init__(self, backend: Backend, **kwargs: Any):
        """
        Initialize API adapter.

        Args:
            backend: Backend to use ('fastapi', 'flask', 'aiohttp')
            **kwargs: Backend-specific arguments
        """
        self.backend = backend
        self.kwargs = kwargs
        self._server: Optional[IAPIServer] = None

    def get_server(self) -> IAPIServer:
        """
        Get API server.

        Returns:
            IAPIServer: Server implementing IAPIServer interface

        Raises:
            APIError: If backend not available or server creation failed
        """
        if self._server is not None:
            return self._server

        if self.backend == "fastapi":
            try:
                from ..infra.fastapi import FastAPIServer

                self._server = FastAPIServer(**self.kwargs)
            except ImportError:
                raise APIError("FastAPI not available. Install: pip install zsys[api]")

        elif self.backend == "flask":
            try:
                from ..infra.flask import FlaskServer

                self._server = FlaskServer(**self.kwargs)
            except ImportError:
                raise APIError(
                    "Flask not available. Install: pip install zsys[api-flask]"
                )

        elif self.backend == "aiohttp":
            try:
                from ..infra.aiohttp import AiohttpServer

                self._server = AiohttpServer(**self.kwargs)
            except ImportError:
                raise APIError(
                    "Aiohttp not available. Install: pip install zsys[api-aiohttp]"
                )

        else:
            raise APIError(
                f"Unknown API backend: {self.backend}. "
                f"Available: fastapi, flask, aiohttp"
            )

        return self._server


__all__ = ["APIAdapter", "Backend"]
