"""zsys.log - Logging module.

Exposes colored console logging, rotating file output, socket-based log
streaming, and memory-managed log queues for the ZSYS ecosystem.
Use ``get_logger`` for simple loggers or ``ColorPrinter`` for the full
feature set including async socket delivery and buffer statistics.
"""
# RU: Модуль логирования ZSYS.
# RU: Цветной вывод, ротация файлов, потоковая отправка через сокет
# RU: и управление памятью для очереди логов.

from .base import BaseLogger
from .printer import (
    ColoredFormatter,
    ColorLogger,
    ColorPrinter,
    Colors,
    get_logger,
    logger,
    printer,
    unified_logger,
)

__all__ = [
    "BaseLogger",
    "get_logger",
    "Colors",
    "ColoredFormatter",
    "ColorLogger",
    "ColorPrinter",
    "logger",
    "printer",
    "unified_logger",
]
