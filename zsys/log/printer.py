"""
ZSYS Printer - Unified logging module.

Combines ColorLogger and UnifiedLogger functionality into a single module.
Provides colored output, file rotation, socket streaming, and memory management.
"""
# RU: Объединённый модуль логирования ZSYS.

import asyncio
import json
import logging
import sys
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union
from logging.handlers import RotatingFileHandler

try:
    from colorlog import ColoredFormatter as _ColorlogFormatter

    _HAS_COLORLOG = True
except ImportError:
    _HAS_COLORLOG = False

try:
    from zsys._core import (
        format_json_log as _c_format_json_log,
        ansi_color as _c_ansi_color,
        print_box_str as _c_print_box_str,
        print_separator_str as _c_print_separator_str,
        print_table_str as _c_print_table_str,
        print_progress_str as _c_print_progress_str,
        C_AVAILABLE as _C,
    )
except ImportError:
    _C = False

# Import base Logger from core
# RU: Импортируем базовый Logger из core
from .base import BaseLogger


# ===== ANSI Colors =====
# RU: ANSI-цвета


class Colors:
    """ANSI escape codes for colored terminal output."""

    # RU: ANSI escape коды для цветного вывода.
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    # Logging level color assignments
    # RU: Уровни логирования
    DEBUG_COLOR = CYAN
    INFO_COLOR = GREEN
    WARNING_COLOR = YELLOW
    ERROR_COLOR = RED
    CRITICAL_COLOR = f"{RED}{BOLD}"


# ===== Formatters =====
# RU: Форматтеры


class ColoredFormatter(logging.Formatter):
    """Colored log formatter — uses colorlog if available, falls back to manual ANSI."""

    # RU: Форматтер с цветным выводом — использует colorlog если доступен.

    _LOG_COLORS = {
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "red,bg_white",
    }
    # Format matches original: level is colored, message is blue
    # RU: Формат идентичен оригиналу: уровень цветной, сообщение синее
    _FMT = "%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(message)s"

    def __new__(cls, *args, **kwargs):
        """Create formatter instance, delegating to colorlog if available.

        Returns:
            ColorlogFormatter if colorlog is installed, otherwise a plain instance.
        """
        # RU: Создаёт экземпляр форматтера, делегируя colorlog если доступен.
        if _HAS_COLORLOG:
            return _ColorlogFormatter(
                cls._FMT,
                log_colors=cls._LOG_COLORS,
            )
        return super().__new__(cls)

    def __init__(self, fmt=None, datefmt=None):
        """Initialize formatter with ANSI fallback when colorlog is unavailable.

        Args:
            fmt: Log format string (unused when colorlog is active).
            datefmt: Date format string.
        """
        # RU: Инициализирует форматтер с ANSI-резервом когда colorlog недоступен.
        if _HAS_COLORLOG:
            return  # Already created via __new__
            # RU: Уже создан через __new__
        # Fallback without colorlog — apply ANSI manually
        # RU: Резервный путь без colorlog — применяем ANSI вручную
        LEVEL_COLORS = {
            "DEBUG": Colors.CYAN,
            "INFO": Colors.GREEN,
            "WARNING": Colors.YELLOW,
            "ERROR": Colors.RED,
            "CRITICAL": Colors.CRITICAL_COLOR,
        }
        self._level_colors = LEVEL_COLORS
        super().__init__("%(levelname)-8s %(message)s", datefmt)

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record with ANSI color codes applied to level and message.

        Args:
            record: Log record to format.

        Returns:
            Formatted log string with ANSI color codes.
        """
        # RU: Форматирует лог-запись с применением ANSI-кодов цвета к уровню и сообщению.
        orig = record.levelname
        color = self._level_colors.get(orig, Colors.RESET)
        record.levelname = f"{color}{orig}{Colors.RESET}"
        msg_color = Colors.BLUE
        record.msg = f"{msg_color}{record.msg}{Colors.RESET}"
        result = super().format(record)
        record.levelname = orig
        return result


# ===== ColorLogger =====
# RU: ColorLogger


class ColorLogger(BaseLogger):
    """
    Logger with colored output and file rotation support.

    Inherits from the base Logger in zsys.core.logging and extends it
    with colored output and file rotation capabilities.

    Attributes:
        name: Logger name.
        logger: logging.Logger instance.
        log_file: Path to the log file.

    Example:
        logger = ColorLogger("myapp", log_file="app.log", level="debug")
        logger.info("Started")
        logger.error("Something went wrong")
    """

    # RU: Логгер с поддержкой цветного вывода и ротации файлов.

    COLORS = Colors

    def __init__(
        self,
        name: str = "core",
        log_file: Optional[Union[str, Path]] = None,
        level: str = "info",
        enable_console: bool = True,
        max_bytes: int = 5 * 1024 * 1024,  # 5 MB
        backup_count: int = 3,
    ):
        """
        Initialize logger with handlers and optional file rotation.

        Args:
            name: Logger name.
            log_file: Path to log file (optional).
            level: Logging level (debug, info, warning, error, critical).
            enable_console: Enable console output.
            max_bytes: Maximum log file size before rotation.
            backup_count: Number of backup files to keep.
        """
        # RU: Инициализирует логгер с обработчиками и опциональной ротацией файлов.
        # Initialize base logger without handlers (we'll add custom ones)
        # RU: Инициализируем базовый логгер без обработчиков (добавим свои)
        super().__init__(name=name, level=level.upper(), format_string=None)

        self.log_file = str(log_file) if log_file else None

        # Clear handlers from the base class to set up custom ones
        # RU: Очищаем handler'ы базового класса
        self.logger.handlers.clear()
        self.logger.propagate = False

        # Console handler with ANSI color formatting
        # RU: Консольный обработчик с цветами
        if enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(ColoredFormatter())
            self.logger.addHandler(console_handler)

        # File handler with automatic rotation
        # RU: Файловый обработчик с ротацией
        if self.log_file:
            Path(self.log_file).parent.mkdir(parents=True, exist_ok=True)
            file_formatter = logging.Formatter(
                "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            file_handler = RotatingFileHandler(
                self.log_file,
                encoding="utf-8",
                maxBytes=max_bytes,
                backupCount=backup_count,
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

    def set_level(self, level: Union[str, int]) -> None:
        """Set the logging level.

        Args:
            level: Logging level as string or integer constant.
        """
        # RU: Устанавливает уровень логирования.
        # Use base class implementation
        # RU: Используем реализацию базового класса
        super().set_level(level)

    # All core logging methods (debug, info, warning, error, critical, exception)
    # are inherited from the base Logger class
    # RU: Все основные методы логирования (debug, info, warning, error, critical, exception)
    # RU: наследуются от базового Logger класса

    # === Helper Methods ===
    # RU: Вспомогательные методы

    def print_color(self, text: str, color: str = "white") -> None:
        """
        Print colored text to the console.

        Args:
            text: Text to print.
            color: Color name (black, red, green, yellow, blue, magenta, cyan, white).
        """
        # RU: Выводит цветной текст в консоль.
        color_map = {
            "black": Colors.BLACK,
            "red": Colors.RED,
            "green": Colors.GREEN,
            "yellow": Colors.YELLOW,
            "blue": Colors.BLUE,
            "magenta": Colors.MAGENTA,
            "cyan": Colors.CYAN,
            "white": Colors.WHITE,
        }
        color_code = color_map.get(color.lower(), Colors.WHITE)
        print(f"{color_code}{text}{Colors.RESET}")

    def prompt_input(self, prompt_text: str, color: str = "blue") -> str:
        """
        Display a colored prompt and read user input.

        Args:
            prompt_text: Prompt text to display.
            color: Prompt color name.

        Returns:
            The string entered by the user.
        """
        # RU: Цветной prompt для ввода пользователя.
        self.print_color(prompt_text, color)
        return input("> ")

    def enable(self) -> None:
        """Enable logging."""
        # RU: Включает логирование.
        self.logger.disabled = False

    def disable(self) -> None:
        """Disable logging."""
        # RU: Отключает логирование.
        self.logger.disabled = True


# ===== ColorPrinter (extends ColorLogger) =====
# RU: ColorPrinter (расширяет ColorLogger)


class ColorPrinter(ColorLogger):
    """Advanced logger with socket streaming and memory management.

    Inherits from ColorLogger and extends it with socket streaming,
    memory management, and asynchronous processing capabilities.

    Features:
    - Colored console output
    - File rotation
    - Socket-based log streaming (for API dashboard)
    - Memory-limited log queue
    - Multiple logger instance management

    Example:
        logger = ColorPrinter(
            name="api",
            log_file="logs/api.log",
            socket_ip="127.0.0.1",
            socket_port=9999
        )
        await logger.connect_socket()
        logger.info("Message will be logged and streamed")
    """

    # RU: Расширенный логгер с потоковой передачей через сокет и управлением памятью.

    COLORS = {
        "black": "\033[30m",
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m",
    }
    RESET = "\033[0m"

    # Class-level tracking of file handlers and active instances
    # RU: Хранение файловых обработчиков и активных экземпляров на уровне класса
    _file_handlers: Dict[str, logging.Handler] = {}
    _logger_instances: Set[str] = set()

    def __init__(
        self,
        name: str = "ColorPrinter",
        log_file: Optional[str] = None,
        log_level: str = "info",
        memory_limit_mb: Optional[float] = None,
        socket_ip: Optional[str] = None,
        socket_port: Optional[int] = None,
        enable_logging: bool = True,
        enable_console: bool = True,
        max_bytes: int = 5 * 1024 * 1024,
        backup_count: int = 3,
    ):
        """Initialize custom logger with extended features.

        Args:
            name: Logger name.
            log_file: Path to log file.
            log_level: Logging level (debug, info, warning, error, critical).
            memory_limit_mb: Memory limit for log queue in MB.
            socket_ip: IP for socket streaming.
            socket_port: Port for socket streaming.
            enable_logging: Enable/disable logging.
            enable_console: Enable console output.
            max_bytes: Maximum log file size before rotation.
            backup_count: Number of backup files to keep.
        """
        # RU: Инициализирует расширенный логгер с дополнительными возможностями.
        # Initialize ColorLogger (parent class)
        # RU: Инициализируем ColorLogger (родительский класс)
        super().__init__(
            name=name,
            log_file=log_file,
            level=log_level,
            enable_console=enable_console,
            max_bytes=max_bytes,
            backup_count=backup_count,
        )

        self._log_level = log_level
        self._enable_logging = enable_logging

        # Memory management for log queue size control
        # RU: Управление памятью для контроля размера очереди логов
        self.memory_limit = memory_limit_mb * 1024 * 1024 if memory_limit_mb else None
        self.current_size = 0
        self.log_queue: deque[str] = deque()
        self.lock = asyncio.Lock()

        # Socket connection state for log streaming
        # RU: Состояние сокетного соединения для потоковой передачи логов
        self.socket_writer: Optional[asyncio.StreamWriter] = None
        self.socket_ip = socket_ip
        self.socket_port = socket_port

        # Register this logger instance for class-level tracking
        # RU: Регистрируем экземпляр логгера для отслеживания на уровне класса
        ColorPrinter._logger_instances.add(name)

        if not self._enable_logging:
            self.logger.disabled = True

    # ===== Socket Management =====
    # RU: Управление сокетом

    async def _send_to_socket(self, message: str):
        """Send log message to socket server.

        Args:
            message: Encoded log message to send.
        """
        # RU: Отправляет лог-сообщение на сокет-сервер.
        if not self.socket_writer:
            return

        try:
            self.socket_writer.write(message.encode("utf-8"))
            await self.socket_writer.drain()
        except Exception:
            self.socket_writer = None

    async def connect_socket(self):
        """Connect to socket server for log streaming."""
        # RU: Подключается к сокет-серверу для потоковой передачи логов.
        if not self.socket_ip or not self.socket_port:
            return

        try:
            reader, writer = await asyncio.open_connection(
                self.socket_ip, self.socket_port
            )
            self.socket_writer = writer
            # Start the batch send loop as a background task
            # RU: Запускаем батчевый цикл отправки
            asyncio.create_task(self._send_logs_loop())
        except Exception:
            self.socket_writer = None

    async def disconnect_socket(self):
        """Disconnect from socket server and clean up the writer."""
        # RU: Отключается от сокет-сервера и очищает writer.
        if self.socket_writer:
            try:
                self.socket_writer.close()
                await self.socket_writer.wait_closed()
            except Exception:
                pass
            self.socket_writer = None

    async def _add_log_async(self, log_entry: str) -> None:
        """Write log entry to the memory-managed buffer queue.

        Args:
            log_entry: JSON-formatted log string to buffer.
        """
        # RU: Запись лога в буферную очередь с управлением памятью.
        entry_size = len(log_entry.encode("utf-8"))
        async with self.lock:
            if self.memory_limit is not None:
                while (
                    self.current_size + entry_size > self.memory_limit
                    and self.log_queue
                ):
                    removed = self.log_queue.popleft()
                    self.current_size -= len(removed.encode("utf-8"))
            self.log_queue.append(log_entry)
            self.current_size += entry_size

    async def _send_logs_loop(self) -> None:
        """Batch loop for sending buffered logs through socket once per second."""
        # RU: Батчевый цикл отправки логов через сокет (раз в секунду).
        while self.socket_writer and not self.socket_writer.is_closing():
            await asyncio.sleep(1)
            async with self.lock:
                if not self.log_queue:
                    continue
                batch = list(self.log_queue)
                self.log_queue.clear()
                self.current_size = 0
            try:
                for line in batch:
                    self.socket_writer.write(line.encode("utf-8") + b"\n")
                await self.socket_writer.drain()
            except Exception as e:
                self.error(f"Socket send error: {e}")
                self.socket_writer = None
                break

    def _format_json_log(self, level: str, message: str) -> str:
        """Format a log record as a JSON string.

        Args:
            level: Log level name (uppercase).
            message: Log message text.

        Returns:
            JSON-encoded log entry string.
        """
        # RU: Форматирует лог-запись в JSON.
        ts = datetime.now().isoformat()
        if _C:
            return _c_format_json_log(level, message, ts)
        return json.dumps(
            {
                "timestamp": ts,
                "level": level,
                "logger": self.name,
                "message": message,
            },
            ensure_ascii=False,
        )

    # ===== Extended Logging Methods =====
    # RU: Расширенные методы логирования

    def _log_and_queue(self, level: str, message: str, *args, **kwargs) -> None:
        """Log a message and add it to the buffer and socket queue.

        Args:
            level: Log level name (debug, info, warning, error, critical).
            message: Message to log.
            *args: Additional positional arguments for the logger.
            **kwargs: Additional keyword arguments for the logger.
        """
        # RU: Логирует сообщение и добавляет в буфер/сокет.
        getattr(super(), level)(message, *args, **kwargs)
        json_entry = self._format_json_log(level.upper(), message)
        # Write to buffer and socket asynchronously if an event loop is running
        # RU: Пишем в буфер и сокет асинхронно если есть event loop
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._add_log_async(json_entry))
            if self.socket_writer:
                loop.create_task(self._send_to_socket(json_entry))
        except RuntimeError:
            # No event loop running — append to queue synchronously
            # RU: Нет event loop — просто добавляем в очередь синхронно
            self.log_queue.append(json_entry)

    def debug(self, message: str, *args, **kwargs):
        """Log a DEBUG level message and queue it for socket delivery."""
        # RU: Логирует сообщение уровня DEBUG и помещает в очередь для отправки.
        self._log_and_queue("debug", message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs):
        """Log an INFO level message and queue it for socket delivery."""
        # RU: Логирует сообщение уровня INFO и помещает в очередь для отправки.
        self._log_and_queue("info", message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        """Log a WARNING level message and queue it for socket delivery."""
        # RU: Логирует сообщение уровня WARNING и помещает в очередь для отправки.
        self._log_and_queue("warning", message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs):
        """Log an ERROR level message and queue it for socket delivery."""
        # RU: Логирует сообщение уровня ERROR и помещает в очередь для отправки.
        self._log_and_queue("error", message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs):
        """Log a CRITICAL level message and queue it for socket delivery."""
        # RU: Логирует сообщение уровня CRITICAL и помещает в очередь для отправки.
        self._log_and_queue("critical", message, *args, **kwargs)

    # ===== Extended Printing Features =====
    # RU: Расширенные возможности вывода

    def print_box(self, text: str, color: str = "white", padding: int = 2) -> None:
        """Print text inside a Unicode box border.

        Args:
            text: Text to display inside the box.
            color: Border and text color name.
            padding: Number of spaces to pad each side of the text.
        """
        # RU: Выводит текст внутри рамки из Unicode-символов.
        if _C:
            self.print_color(_c_print_box_str(text, padding), color)
            return
        lines = text.split("\n")
        max_width = max(len(line) for line in lines) + (padding * 2)
        border_top = "╔" + "═" * max_width + "╗"
        border_bottom = "╚" + "═" * max_width + "╝"
        self.print_color(border_top, color)
        for line in lines:
            padded_line = " " * padding + line.ljust(max_width - padding)
            self.print_color(f"║{padded_line}║", color)
        self.print_color(border_bottom, color)

    def print_separator(
        self, char: str = "═", length: int = 60, color: str = "cyan"
    ) -> None:
        """Print a horizontal separator line of the given character.

        Args:
            char: Character used to draw the separator.
            length: Total length of the separator line.
            color: Color name for the separator.
        """
        # RU: Выводит горизонтальный разделитель из заданного символа.
        if _C:
            self.print_color(_c_print_separator_str(char, length), color)
            return
        self.print_color(char * length, color)

    def print_banner(self, text: str, color: str = "green") -> None:
        """
        Print a large banner with separator lines above and below the text.

        Args:
            text: Text to display in the banner.
            color: Banner color name.
        """
        # RU: Выводит большой баннер с разделителями сверху и снизу текста.
        length = len(text) + 4
        self.print_separator("═", length, color)
        self.print_color(f"  {text}  ", color)
        self.print_separator("═", length, color)

    def print_table(
        self, headers: list[str], rows: list[list[str]], color: str = "white"
    ) -> None:
        """Print a formatted Unicode table with headers and rows.

        Args:
            headers: Column header labels.
            rows: List of rows, each a list of cell strings.
            color: Table color name.
        """
        # RU: Выводит форматированную Unicode-таблицу с заголовками и строками.
        if _C:
            self.print_color(_c_print_table_str(headers, rows), color)
            return
        # Calculate column widths
        # RU: Вычисляем ширину столбцов
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))

        # Print header
        # RU: Выводим заголовок
        header_line = (
            "│ "
            + " │ ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
            + " │"
        )
        separator = "├" + "┼".join("─" * (w + 2) for w in col_widths) + "┤"
        top = "┌" + "┬".join("─" * (w + 2) for w in col_widths) + "┐"
        bottom = "└" + "┴".join("─" * (w + 2) for w in col_widths) + "┘"

        self.print_color(top, color)
        self.print_color(header_line, color)
        self.print_color(separator, color)

        # Print rows
        # RU: Выводим строки
        for row in rows:
            row_line = (
                "│ "
                + " │ ".join(
                    str(cell).ljust(col_widths[i]) for i, cell in enumerate(row)
                )
                + " │"
            )
            self.print_color(row_line, color)

        self.print_color(bottom, color)

    def print_progress(
        self, current: int, total: int, prefix: str = "Progress", length: int = 40
    ) -> None:
        """Print a progress bar showing completion percentage.

        Args:
            current: Current progress value.
            total: Total value representing 100% completion.
            prefix: Label displayed before the bar.
            length: Character width of the progress bar.
        """
        # RU: Выводит прогресс-бар с процентом выполнения.
        if _C:
            percent = 100 * (current / float(total)) if total else 0
            color = (
                "green" if percent >= 100 else ("yellow" if percent >= 50 else "red")
            )
            self.print_color(
                _c_print_progress_str(current, total, prefix, length), color
            )
            return
        percent = 100 * (current / float(total))
        filled = int(length * current // total)
        bar = "█" * filled + "░" * (length - filled)

        if percent >= 100:
            color = "green"
        elif percent >= 50:
            color = "yellow"
        else:
            color = "red"

        self.print_color(f"{prefix}: |{bar}| {percent:.1f}% ({current}/{total})", color)

    def enable(self):
        """Enable logging."""
        # RU: Включает логирование.
        self.logger.disabled = False
        self._enable_logging = True

    def disable(self):
        """Disable logging."""
        # RU: Отключает логирование.
        self.logger.disabled = True
        self._enable_logging = False

    # ===== Log Buffer Management =====
    # RU: Управление буфером логов

    async def get_logs(self, limit: Optional[int] = None) -> List[str]:
        """
        Return stored logs from the buffer.

        Args:
            limit: Maximum number of recent entries to return (None = all).

        Returns:
            List of JSON log entry strings.
        """
        # RU: Возвращает сохранённые логи из буфера.
        async with self.lock:
            logs = list(self.log_queue)
        return logs[-limit:] if limit else logs

    async def get_stats(self) -> Dict[str, Any]:
        """
        Return log buffer statistics.

        Returns:
            Dict with count, memory_used_kb, memory_limit_kb, socket_connected.
        """
        # RU: Возвращает статистику буфера логов.
        async with self.lock:
            count = len(self.log_queue)
            size_kb = self.current_size / 1024
        return {
            "logger": self.name,
            "count": count,
            "memory_used_kb": round(size_kb, 2),
            "memory_limit_kb": round(self.memory_limit / 1024, 2)
            if self.memory_limit
            else None,
            "socket_connected": self.socket_writer is not None,
            "level": logging.getLevelName(self.logger.level),
        }

    def set_memory_limit(self, mb: Optional[float]) -> None:
        """
        Set memory limit for the log buffer at runtime.

        Args:
            mb: Limit in megabytes (None = no limit).
        """
        # RU: Устанавливает лимит памяти для буфера логов на лету.
        self.memory_limit = mb * 1024 * 1024 if mb else None

    @classmethod
    def cleanup(cls) -> None:
        """Clear the logger instance registry and file handler table."""
        # RU: Очищает реестр инстансов логгеров.
        cls._logger_instances.clear()
        cls._file_handlers.clear()


# ===== Factory Functions =====
# RU: Фабричные функции


def get_logger(
    name: str = "core",
    level: str = "info",
    log_file: Optional[Union[str, Path]] = None,
    **kwargs,
) -> ColorLogger:
    """
    Factory function for creating ColorLogger instances.

    Args:
        name: Logger name.
        level: Logging level.
        log_file: Path to log file.
        **kwargs: Additional parameters forwarded to ColorLogger.

    Returns:
        Configured ColorLogger instance.

    Example:
        logger = get_logger("myapp", level="debug", log_file="logs/app.log")
    """
    # RU: Фабрика для создания экземпляров ColorLogger.
    return ColorLogger(name=name, level=level, log_file=log_file, **kwargs)


# ===== Global Instances =====
# RU: Глобальные экземпляры

# Main logger for core/ modules
# RU: Основной логгер для core/
logger = ColorLogger(name="core", level="info")

# Printer for user-facing output (extended features)
# RU: Принтер для пользовательского вывода (расширенный)
printer = ColorPrinter(name="printer", log_level="info")

# Unified logger for production use
# RU: Unified logger для продакшена
unified_logger = ColorPrinter(name="zsys", log_level="info", enable_logging=True)


__all__ = [
    # Classes
    # RU: Классы
    "Colors",
    "ColoredFormatter",
    "ColorLogger",
    "ColorPrinter",
    # Functions
    # RU: Функции
    "get_logger",
    # Global instances
    # RU: Глобальные экземпляры
    "logger",
    "printer",
    "unified_logger",
]
