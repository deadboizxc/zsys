"""
Base abstractions for API servers.

Defines interfaces for web API implementations across zsys ecosystem.

⭐ UNIFIED CONFIG: APIConfig now inherits from BaseConfig for consistency
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# Import BaseConfig from zsys.core
from zsys.core.config import BaseConfig, Field


class APIConfig(BaseConfig):
    """
    Configuration for API server - extends universal BaseConfig.

    Now uses Pydantic BaseConfig instead of dataclass.
    Inherits common fields: app_name, debug, log_level
    """

    host: str = Field(default="0.0.0.0", description="API server host")
    port: int = Field(default=8000, description="API server port")
    secret_key: str = Field(
        default="default-secret-key", description="Secret key for authentication"
    )
    admin_username: str = Field(default="admin", description="Admin username")
    admin_password: str = Field(default="admin", description="Admin password")
    templates_dir: Optional[Path] = Field(
        default=None, description="Templates directory"
    )
    static_dir: Optional[Path] = Field(
        default=None, description="Static files directory"
    )
    enable_cors: bool = Field(default=True, description="Enable CORS")
    enable_websocket: bool = Field(default=True, description="Enable WebSocket support")
    max_log_entries: int = Field(
        default=1000, description="Maximum log entries to store"
    )

    class Config:
        env_prefix = "API_"


class BaseAPI(ABC):
    """Abstract base class for API servers.

    Provides common interface for web API implementations:
    - FastAPI
    - Flask
    - Aiohttp
    - Custom implementations
    """

    def __init__(self, config: APIConfig):
        """Initialize API server.

        Args:
            config: API configuration
        """
        self.config = config
        self._running = False
        self._logs: List[Dict[str, Any]] = []
        self._websocket_clients: List[Any] = []

    @abstractmethod
    def setup(self) -> None:
        """Setup API server (routes, middleware, etc.)."""
        pass

    @abstractmethod
    def start(self, threaded: bool = True) -> None:
        """Start API server.

        Args:
            threaded: Run in background thread (default True)
        """
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop API server."""
        pass

    @abstractmethod
    def add_route(
        self, path: str, handler: Callable, methods: List[str] = None
    ) -> None:
        """Add custom route.

        Args:
            path: URL path
            handler: Handler function
            methods: HTTP methods (GET, POST, etc.)
        """
        pass

    @abstractmethod
    async def broadcast(self, message: Dict[str, Any]) -> None:
        """Broadcast message to all WebSocket clients.

        Args:
            message: Message to broadcast
        """
        pass

    def add_log(self, log_entry: Dict[str, Any]) -> None:
        """Add log entry to internal storage.

        Args:
            log_entry: Log entry dict
        """
        self._logs.append(log_entry)
        if len(self._logs) > self.config.max_log_entries:
            self._logs.pop(0)

    def get_logs(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get stored log entries.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of log entries
        """
        if limit:
            return self._logs[-limit:]
        return self._logs

    def get_stats(self) -> Dict[str, Any]:
        """Get API server statistics.

        Returns:
            Statistics dict
        """
        return {
            "running": self._running,
            "total_logs": len(self._logs),
            "ws_connections": len(self._websocket_clients),
            "config": {
                "host": self.config.host,
                "port": self.config.port,
                "websocket_enabled": self.config.enable_websocket,
            },
        }

    @property
    def is_running(self) -> bool:
        """Check if server is running."""
        return self._running
