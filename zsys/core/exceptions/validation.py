
"""Validation exceptions."""

from typing import Optional, Dict, Any
from .base import BaseException


class ValidationError(BaseException):
    """Data validation errors."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize validation error.
        
        Args:
            message: Error message
            field: Field name that failed validation
            details: Additional details
        """
        super().__init__(message, code="VALIDATION_ERROR", details=details)
        self.field = field


__all__ = [
    "ValidationError",
]
