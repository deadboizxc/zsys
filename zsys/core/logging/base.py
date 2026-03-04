# Backward compatibility shim — actual implementation is in zsys.log.base
# RU: Обратная совместимость — реализация переехала в zsys.log.base
from zsys.log.base import BaseLogger, get_logger

__all__ = ["BaseLogger", "get_logger"]
