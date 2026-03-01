"""
ZSYS Core Logging Module.

Provides base logging functionality for the ZSYS ecosystem.

Components:
- BaseLogger: Foundation logger class with context support
- Logger: Alias for BaseLogger (backward compatibility)
- get_logger: Factory function for creating logger instances

Features:
- Flexible log level management
- Handler management
- Context support for structured logging
- Thread-safe operations
- Child logger creation
- State management (enable/disable)

Usage:
    # Simple usage
    from zsys.core.logging import Logger
    
    logger = Logger("myapp")
    logger.info("Application started")
    logger.error("Error occurred", exc_info=True)
    
    # With context
    with logger.context(user_id=123):
        logger.info("User action")
    
    # Bound logger
    user_logger = logger.bind(user_id=123)
    user_logger.info("Action")
    
    # Child logger
    sub_logger = logger.get_child("submodule")
    sub_logger.debug("Debug info")
"""

from .base import BaseLogger, get_logger

# Backward compatibility alias
Logger = BaseLogger

__all__ = [
    "BaseLogger",
    "Logger",
    "get_logger",
]
