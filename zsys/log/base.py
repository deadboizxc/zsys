"""BaseLogger implementation for the ZSYS ecosystem.

Moved from zsys.core.logging.base — concrete implementation of ILogger.
"""
# RU: Реализация BaseLogger переехала сюда из zsys.core.logging.base.

import logging
import sys
from typing import Optional, Dict, Any, Union
from contextlib import contextmanager

from zsys.core.logging.interface import ILogger  # noqa: F401 — kept for type checking


class BaseLogger:
    """
    Base logger class for ZSYS ecosystem.

    Provides core logging functionality that can be extended by subclasses
    with additional features like colors, file rotation, socket streaming, etc.

    Attributes:
        name: Logger name (usually module/component name)
        logger: Internal logging.Logger instance
        level: Current log level

    Usage:
        logger = BaseLogger("myapp")
        logger.info("Application started")
        logger.error("Error occurred", exc_info=True)

        # With context
        with logger.context(user_id=123):
            logger.info("User action")  # Will include user_id in log
    """

    # RU: Базовый класс логгера — обёртка над logging.Logger с контекстом и удобным API.

    def __init__(
        self,
        name: str,
        level: Union[str, int] = "INFO",
        format_string: Optional[str] = None,
        datefmt: Optional[str] = None,
        propagate: bool = False,
    ):
        """
        Initialize base logger.

        Args:
            name: Logger name (usually module name)
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL) or int
            format_string: Custom format string for log messages
            datefmt: Date format string
            propagate: Whether to propagate logs to parent loggers
        """
        # RU: Сохраняет параметры, получает или создаёт именованный logger и настраивает обработчик.
        self.name = name
        self._level = self._normalize_level(level)
        self._format_string = format_string
        self._datefmt = datefmt
        self._context_data: Dict[str, Any] = {}

        # Get or create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self._level)
        self.logger.propagate = propagate

        # Initialize handlers if not already set
        if not self.logger.handlers:
            self._setup_default_handler()

    def _normalize_level(self, level: Union[str, int]) -> int:
        """Normalize log level to integer."""
        if isinstance(level, int):
            return level

        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "WARN": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
            "FATAL": logging.CRITICAL,
        }

        return level_map.get(level.upper(), logging.INFO)

    def _setup_default_handler(self):
        """Set up the default console (stdout) handler with a standard formatter."""
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(self._level)

        if self._format_string is None:
            self._format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

        formatter = logging.Formatter(self._format_string, datefmt=self._datefmt)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def _build_message(self, message: str) -> str:
        """Build message with context data."""
        if not self._context_data:
            return message

        context_str = " ".join(f"{k}={v}" for k, v in self._context_data.items())
        return f"{message} [{context_str}]"

    # ===== Core Logging Methods =====

    def debug(self, message: str, *args, **kwargs):
        self.logger.debug(self._build_message(message), *args, **kwargs)

    def info(self, message: str, *args, **kwargs):
        self.logger.info(self._build_message(message), *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        self.logger.warning(self._build_message(message), *args, **kwargs)

    def warn(self, message: str, *args, **kwargs):
        """Alias for warning()."""
        self.warning(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs):
        self.logger.error(self._build_message(message), *args, **kwargs)

    def critical(self, message: str, *args, **kwargs):
        self.logger.critical(self._build_message(message), *args, **kwargs)

    def fatal(self, message: str, *args, **kwargs):
        """Alias for critical()."""
        self.critical(message, *args, **kwargs)

    def exception(self, message: str, *args, **kwargs):
        """Log exception with traceback."""
        kwargs.setdefault("exc_info", True)
        self.logger.exception(self._build_message(message), *args, **kwargs)

    def log(self, level: Union[str, int], message: str, *args, **kwargs):
        """Log message with specific level."""
        level = self._normalize_level(level)
        self.logger.log(level, self._build_message(message), *args, **kwargs)

    # ===== Level Management =====

    def set_level(self, level: Union[str, int]):
        """Set logging level."""
        self._level = self._normalize_level(level)
        self.logger.setLevel(self._level)

        for handler in self.logger.handlers:
            handler.setLevel(self._level)

    def get_level(self) -> int:
        """Get current logging level."""
        return self._level

    def is_enabled_for(self, level: Union[str, int]) -> bool:
        """Check if logger is enabled for given level."""
        level = self._normalize_level(level)
        return self.logger.isEnabledFor(level)

    # ===== Handler Management =====

    def add_handler(self, handler: logging.Handler):
        """Add logging handler."""
        self.logger.addHandler(handler)

    def remove_handler(self, handler: logging.Handler):
        """Remove logging handler."""
        self.logger.removeHandler(handler)

    def clear_handlers(self):
        """Remove all handlers from the logger."""
        self.logger.handlers.clear()

    def get_handlers(self):
        """Get all handlers."""
        return self.logger.handlers.copy()

    # ===== Context Management =====

    @contextmanager
    def context(self, **kwargs):
        """Context manager for adding context to logs."""
        old_context = self._context_data.copy()
        self._context_data.update(kwargs)
        try:
            yield self
        finally:
            self._context_data = old_context

    def bind(self, **kwargs) -> "BaseLogger":
        """Create new logger with bound context."""
        new_logger = self.__class__(
            name=self.name,
            level=self._level,
            format_string=self._format_string,
            datefmt=self._datefmt,
        )
        new_logger._context_data = {**self._context_data, **kwargs}
        new_logger.logger = self.logger
        return new_logger

    # ===== State Management =====

    def enable(self):
        """Enable logging."""
        self.logger.disabled = False

    def disable(self):
        """Disable logging."""
        self.logger.disabled = True

    def is_disabled(self) -> bool:
        """Check if logger is disabled."""
        return self.logger.disabled

    # ===== Utility Methods =====

    def get_child(self, suffix: str) -> "BaseLogger":
        """Get child logger."""
        child_name = f"{self.name}.{suffix}"
        return self.__class__(
            name=child_name,
            level=self._level,
            format_string=self._format_string,
            datefmt=self._datefmt,
        )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}', level={self._level})>"


# ===== Factory Functions =====


def get_logger(
    name: str, level: Union[str, int] = "INFO", format_string: Optional[str] = None
) -> BaseLogger:
    """
    Factory function to create logger instance.

    Args:
        name: Logger name
        level: Log level
        format_string: Custom format string

    Returns:
        BaseLogger instance
    """
    return BaseLogger(name=name, level=level, format_string=format_string)


__all__ = ["BaseLogger", "get_logger"]
