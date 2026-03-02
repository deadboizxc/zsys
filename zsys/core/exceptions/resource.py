"""ZSYS resource exceptions — not-found and permission errors.

Raised when requested resources are absent or the caller lacks
sufficient permissions to access them.
"""
# RU: Исключения ресурсов — ошибки «не найдено» и отказа в доступе.
# RU: Возникают при отсутствии запрошенных ресурсов или недостатке прав.

from .base import BaseException


class NotFoundError(BaseException):
    """Exception raised when a requested resource cannot be located.

    Raised by storage, ORM, and service layers when a lookup by ID,
    key, or path returns no result.

    Attributes:
        message: Human-readable error description.
        code: Optional error code string.
    """
    # RU: Исключение при отсутствии запрошенного ресурса.
    pass


class PermissionError(BaseException):
    """Exception raised when the caller lacks permission for an operation.

    Raised by access-control layers when a user or client tries to perform
    an action they are not authorised to do.

    Attributes:
        message: Human-readable error description.
        code: Optional error code string.
    """
    # RU: Исключение при отсутствии прав для выполнения операции.
    pass


class PermissionDeniedError(BaseException):
    """Exception raised when a specific named action is denied.

    A more specific variant of PermissionError that records which
    action was denied for easier debugging and audit logging.

    Attributes:
        message: Human-readable error description including the action.
        action: The action string that was denied.
    """
    # RU: Исключение при отказе в выполнении конкретного именованного действия.

    def __init__(self, action: str, code: str | None = None):
        """Initialise the error with the denied action description.

        Args:
            action: Human-readable name of the denied action (e.g. ``"delete_user"``).
            code: Optional error code string.
        """
        # RU: Инициализировать с описанием запрещённого действия.
        message = f"Permission denied: {action}"
        super().__init__(message, code)
        self.action = action


__all__ = [
    "NotFoundError",
    "PermissionError",
    "PermissionDeniedError",
]
