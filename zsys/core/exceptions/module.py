"""ZSYS module and file exceptions — loader and filesystem errors.

Raised when module loading, discovery, or file I/O operations fail.
"""
# RU: Исключения модулей и файлов — ошибки загрузчика и файловой системы.
# RU: Возникают при сбоях загрузки модулей или файловых операций.

from .base import BaseException


class ModuleError(BaseException):
    """Exception raised when a plugin module fails to load or operate.

    Raised by the module loader when a module file is missing, contains
    syntax errors, raises an import error, or fails during registration.

    Attributes:
        message: Human-readable error description.
        code: Optional error code string.
    """

    # RU: Исключение при сбое загрузки или работы плагин-модуля.
    pass


class FileError(BaseException):
    """Exception raised when a filesystem operation fails.

    Raised for permission errors, missing files, I/O failures, or
    unsupported path operations outside the allowed working directory.

    Attributes:
        message: Human-readable error description.
        code: Optional error code string.
    """

    # RU: Исключение при сбое файловой операции.
    pass
