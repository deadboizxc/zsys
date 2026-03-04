"""
HTTP clients module.

Provides unified async HTTP client interface with retry logic.
"""

from .base import BaseHttpClient
from .client import (
    AIOHTTP_AVAILABLE,
    HTTPX_AVAILABLE,
    HttpClient,
    RetryConfig,
    request,
)
from .retry import RetryConfig as HttpRetryConfig
from .retry import retry_request

__all__ = [
    "BaseHttpClient",
    "HttpClient",
    "RetryConfig",
    "HttpRetryConfig",
    "retry_request",
    "request",
    "AIOHTTP_AVAILABLE",
    "HTTPX_AVAILABLE",
]
