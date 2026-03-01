"""Base exception classes."""

from typing import Optional, Dict, Any


class BaseException(Exception):
    """
    Base exception for all ZSYS errors.
    
    Features:
    - Optional error code
    - Additional details dictionary
    - Rich error formatting
    """
    
    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize error.
        
        Args:
            message: Error message
            code: Optional error code (e.g., "INVALID_TOKEN")
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
    
    def __str__(self) -> str:
        """String representation."""
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message
    
    def __repr__(self) -> str:
        """Debug representation."""
        return f"{self.__class__.__name__}(message={self.message!r}, code={self.code!r})"


__all__ = [
    "BaseException",
]
