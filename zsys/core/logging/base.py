"""Base Logger for ZSYS Core.

Provides foundational logging functionality that can be extended
by specific implementations (ColorLogger, UnifiedLogger, etc.).
Supports flexible level management, handler management, context, and thread-safety.
"""
# RU: Базовый логгер ядра ZSYS — расширяемая основа для ColorLogger, UnifiedLogger и др.
# RU: Поддерживает управление уровнями, обработчиками, контекстом и дочерними логгерами.

import logging
import sys
from typing import Optional, Dict, Any, Union
from pathlib import Path
from contextlib import contextmanager


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

        # Get or create logger — повторные вызовы с тем же именем вернут тот же экземпляр
        # RU: logging.getLogger возвращает один и тот же объект для одинакового имени (registry).
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self._level)
        self.logger.propagate = propagate

        # Initialize handlers if not already set
        # RU: Пропускаем setup если logger уже настроен (например, при повторном создании).
        if not self.logger.handlers:
            self._setup_default_handler()

    def _normalize_level(self, level: Union[str, int]) -> int:
        """
        Normalize log level to integer.

        Args:
            level: String level name or integer level

        Returns:
            Integer log level
        """
        # RU: Преобразует строковое название уровня в числовой код logging; неизвестное → INFO.
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
        # RU: Создаёт StreamHandler на stdout и применяет стандартный формат если не задан другой.
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(self._level)

        # Default format
        if self._format_string is None:
            self._format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

        formatter = logging.Formatter(self._format_string, datefmt=self._datefmt)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def _build_message(self, message: str) -> str:
        """
        Build message with context data.

        Args:
            message: Original message

        Returns:
            Message with context appended
        """
        # RU: Если контекст не пуст — добавляет пары key=value в квадратных скобках к сообщению.
        if not self._context_data:
            return message

        context_str = " ".join(f"{k}={v}" for k, v in self._context_data.items())
        return f"{message} [{context_str}]"

    # ===== Core Logging Methods =====

    def debug(self, message: str, *args, **kwargs):
        """
        Log debug message.

        Args:
            message: Log message
            *args: Positional arguments for message formatting
            **kwargs: Keyword arguments (exc_info, stack_info, stacklevel, extra)
        """
        # RU: Передаёт сообщение с добавленным контекстом во внутренний logging.Logger.debug.
        self.logger.debug(self._build_message(message), *args, **kwargs)

    def info(self, message: str, *args, **kwargs):
        """
        Log info message.

        Args:
            message: Log message
            *args: Positional arguments for message formatting
            **kwargs: Keyword arguments (exc_info, stack_info, stacklevel, extra)
        """
        # RU: Передаёт сообщение с добавленным контекстом во внутренний logging.Logger.info.
        self.logger.info(self._build_message(message), *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        """
        Log warning message.

        Args:
            message: Log message
            *args: Positional arguments for message formatting
            **kwargs: Keyword arguments (exc_info, stack_info, stacklevel, extra)
        """
        # RU: Передаёт сообщение с добавленным контекстом во внутренний logging.Logger.warning.
        self.logger.warning(self._build_message(message), *args, **kwargs)

    def warn(self, message: str, *args, **kwargs):
        """Alias for warning()."""
        # RU: Псевдоним для обратной совместимости с кодом, использующим warn().
        self.warning(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs):
        """
        Log error message.

        Args:
            message: Log message
            *args: Positional arguments for message formatting
            **kwargs: Keyword arguments (exc_info, stack_info, stacklevel, extra)
        """
        # RU: Передаёт сообщение с добавленным контекстом во внутренний logging.Logger.error.
        self.logger.error(self._build_message(message), *args, **kwargs)

    def critical(self, message: str, *args, **kwargs):
        """
        Log critical message.

        Args:
            message: Log message
            *args: Positional arguments for message formatting
            **kwargs: Keyword arguments (exc_info, stack_info, stacklevel, extra)
        """
        # RU: Передаёт сообщение с добавленным контекстом во внутренний logging.Logger.critical.
        self.logger.critical(self._build_message(message), *args, **kwargs)

    def fatal(self, message: str, *args, **kwargs):
        """Alias for critical()."""
        # RU: Псевдоним для обратной совместимости с кодом, использующим fatal().
        self.critical(message, *args, **kwargs)

    def exception(self, message: str, *args, **kwargs):
        """
        Log exception with traceback.

        Should be called from exception handler.

        Args:
            message: Log message
            *args: Positional arguments for message formatting
            **kwargs: Keyword arguments (exc_info defaults to True)
        """
        # RU: Устанавливает exc_info=True по умолчанию для автоматического захвата трейсбека.
        kwargs.setdefault("exc_info", True)
        self.logger.exception(self._build_message(message), *args, **kwargs)

    def log(self, level: Union[str, int], message: str, *args, **kwargs):
        """
        Log message with specific level.

        Args:
            level: Log level (string or int)
            message: Log message
            *args: Positional arguments for message formatting
            **kwargs: Keyword arguments
        """
        # RU: Нормализует уровень и делегирует logging.Logger.log с добавленным контекстом.
        level = self._normalize_level(level)
        self.logger.log(level, self._build_message(message), *args, **kwargs)

    # ===== Level Management =====

    def set_level(self, level: Union[str, int]):
        """
        Set logging level.

        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL) or int
        """
        # RU: Обновляет уровень логгера и всех его обработчиков одновременно.
        self._level = self._normalize_level(level)
        self.logger.setLevel(self._level)

        # Update all handlers
        for handler in self.logger.handlers:
            handler.setLevel(self._level)

    def get_level(self) -> int:
        """
        Get current logging level.

        Returns:
            Current log level as integer
        """
        # RU: Возвращает числовой уровень, хранящийся в _level (кешируется при set_level).
        return self._level

    def is_enabled_for(self, level: Union[str, int]) -> bool:
        """
        Check if logger is enabled for given level.

        Args:
            level: Log level to check

        Returns:
            True if enabled, False otherwise
        """
        # RU: Нормализует уровень и делегирует проверку стандартному logging.Logger.isEnabledFor.
        level = self._normalize_level(level)
        return self.logger.isEnabledFor(level)

    # ===== Handler Management =====

    def add_handler(self, handler: logging.Handler):
        """
        Add logging handler.

        Args:
            handler: Handler to add
        """
        # RU: Добавляет обработчик во внутренний logging.Logger (например, FileHandler).
        self.logger.addHandler(handler)

    def remove_handler(self, handler: logging.Handler):
        """
        Remove logging handler.

        Args:
            handler: Handler to remove
        """
        # RU: Удаляет конкретный обработчик из внутреннего logging.Logger.
        self.logger.removeHandler(handler)

    def clear_handlers(self):
        """Remove all handlers from the logger."""
        # RU: Очищает список обработчиков, прекращая вывод во все подключённые назначения.
        self.logger.handlers.clear()

    def get_handlers(self):
        """
        Get all handlers.

        Returns:
            List of handlers
        """
        # RU: Возвращает копию списка обработчиков для безопасной итерации снаружи.
        return self.logger.handlers.copy()

    # ===== Context Management =====

    @contextmanager
    def context(self, **kwargs):
        """
        Context manager for adding context to logs.

        Args:
            **kwargs: Context key-value pairs

        Usage:
            with logger.context(user_id=123, request_id="abc"):
                logger.info("Processing request")
        """
        # RU: Сохраняет текущий контекст, добавляет новые поля и восстанавливает при выходе.
        # Save current context
        old_context = self._context_data.copy()

        # Add new context
        self._context_data.update(kwargs)

        try:
            yield self
        finally:
            # Restore old context
            self._context_data = old_context

    def bind(self, **kwargs) -> "BaseLogger":
        """
        Create new logger with bound context.

        Args:
            **kwargs: Context key-value pairs

        Returns:
            New logger instance with bound context

        Usage:
            user_logger = logger.bind(user_id=123)
            user_logger.info("User action")
        """
        # RU: Создаёт новый экземпляр логгера с объединённым контекстом и общим logging.Logger.
        new_logger = self.__class__(
            name=self.name,
            level=self._level,
            format_string=self._format_string,
            datefmt=self._datefmt,
        )
        new_logger._context_data = {**self._context_data, **kwargs}
        new_logger.logger = (
            self.logger
        )  # Share underlying logger — RU: единый backend для всех привязок
        return new_logger

    # ===== State Management =====

    def enable(self):
        """Enable logging."""
        # RU: Снимает флаг disabled с внутреннего logging.Logger.
        self.logger.disabled = False

    def disable(self):
        """Disable logging."""
        # RU: Устанавливает флаг disabled — логгер перестаёт обрабатывать любые записи.
        self.logger.disabled = True

    def is_disabled(self) -> bool:
        """
        Check if logger is disabled.

        Returns:
            True if disabled, False otherwise
        """
        # RU: Читает флаг disabled напрямую из внутреннего logging.Logger.
        return self.logger.disabled

    # ===== Utility Methods =====

    def get_child(self, suffix: str) -> "BaseLogger":
        """
        Get child logger.

        Args:
            suffix: Suffix for child logger name

        Returns:
            Child logger instance

        Usage:
            child = logger.get_child("submodule")
            # Creates logger with name "parent.submodule"
        """
        # RU: Создаёт дочерний логгер с именем «родитель.суффикс» и теми же настройками.
        child_name = f"{self.name}.{suffix}"
        return self.__class__(
            name=child_name,
            level=self._level,
            format_string=self._format_string,
            datefmt=self._datefmt,
        )

    def __repr__(self) -> str:
        """Return a developer-friendly string representation.

        Returns:
            str: Representation showing class name, logger name, and current level.
        """
        # RU: Показывает класс, имя и числовой уровень для удобной отладки в REPL.
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

    Usage:
        logger = get_logger("myapp", level="DEBUG")
    """
    # RU: Удобная фабричная функция — создаёт BaseLogger без явного импорта класса.
    return BaseLogger(name=name, level=level, format_string=format_string)


__all__ = ["BaseLogger", "get_logger"]
