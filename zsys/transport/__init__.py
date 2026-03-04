"""
zsys.transport - Transport Module

Provides HTTP and WebSocket client implementations.

Public API (import from here):
    from zsys.transport import HttpClient, BaseHttpClient

Implementation backends available:
    - HTTP (aiohttp, httpx)
    - WebSocket (websockets, aiohttp)

Usage:
    from zsys.transport import HttpClient
    from zsys.core.integration import ServiceRegistry

    # Create HTTP client
    http = HttpClient(base_url='https://api.example.com')

    # Register
    ServiceRegistry.register('http', http)

    # Use
    response = await http.get('/users')
    data = await response.json()

Installation:
    pip install zsys[transport]        # HTTP + WebSocket
"""

# Import implementations from infra
try:
    from .infra import BaseHttpClient, HttpClient

    HTTP_AVAILABLE = True
except ImportError:
    HttpClient = None
    BaseHttpClient = None
    HTTP_AVAILABLE = False

try:
    from .infra.wss import WebSocketClient

    WSS_AVAILABLE = True
except ImportError:
    WebSocketClient = None
    WSS_AVAILABLE = False

__all__ = [
    "HttpClient",
    "BaseHttpClient",
    "HTTP_AVAILABLE",
    "WebSocketClient",
    "WSS_AVAILABLE",
]


def list_available_backends():
    """Check which transport backends are installed."""
    return {
        "http": HTTP_AVAILABLE,
        "wss": WSS_AVAILABLE,
    }
