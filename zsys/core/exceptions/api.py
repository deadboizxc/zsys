"""API and bot-related exceptions."""

from .base import BaseException


class APIError(BaseException):
    """API/HTTP request errors."""
    
    def __init__(self, message: str, code: str | None = None):
        """Initialize API error.
        
        Args:
            message: Error message
            code: Error code (can be HTTP status code as string)
        """
        super().__init__(message, code)


class BotError(BaseException):
    """Bot operation errors."""
    pass
