"""
Core API Module - Universal web API abstractions for zsys projects.

Provides abstract base classes for:
- Web API servers (FastAPI, Flask, etc.)
- WebSocket servers for real-time communication
- Authentication and authorization
- Logging and monitoring dashboards

Concrete implementations (e.g. FastAPIServer) should live
in your project (e.g. zxc_userbot/core/api/web.py).
"""

from .base import APIConfig, BaseAPI

__all__ = ["BaseAPI", "APIConfig"]
