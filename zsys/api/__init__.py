"""
API Adapters - public API for working with API frameworks.

Provides unified interface for creating API servers.

Usage:
    from zsys.api.adapters import APIAdapter
    
    adapter = APIAdapter(backend='fastapi', host='0.0.0.0', port=8000)
    server = adapter.get_server()  # Returns IAPIServer
"""

from .api_adapter import APIAdapter, Backend

__all__ = ['APIAdapter', 'Backend']
