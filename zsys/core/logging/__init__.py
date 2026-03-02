"""ZSYS Core Logging Module.

Provides base logging functionality for the ZSYS ecosystem.
Exports BaseLogger, its Logger alias, and the get_logger factory function.
"""
# RU: Модуль логирования ядра ZSYS — предоставляет BaseLogger, псевдоним Logger и фабрику get_logger.
# RU: Для создания логгера используйте get_logger("имя") или Logger("имя") напрямую.

from .base import BaseLogger, get_logger

# Backward compatibility alias
Logger = BaseLogger

__all__ = [
    "BaseLogger",
    "Logger",
    "get_logger",
]
