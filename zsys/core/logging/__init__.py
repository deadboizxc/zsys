"""ZSYS Core Logging Module — pure interface/contract only.

Concrete implementations live in zsys.log.
"""
# RU: Модуль логирования ядра ZSYS — только интерфейс (Protocol).
# RU: Реализация BaseLogger и get_logger находится в zsys.log.

from .interface import ILogger, LoggerProtocol

__all__ = ["ILogger", "LoggerProtocol"]
