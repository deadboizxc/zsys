"""
HTTP clients module.

Provides unified async HTTP client interface with retry logic.
"""

from .base import BaseHttpClient
from .client import (
    HttpClient,
    RetryConfig,
    request,
    AIOHTTP_AVAILABLE,
    HTTPX_AVAILABLE,
)
from .retry import RetryConfig as HttpRetryConfig, retry_request

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
