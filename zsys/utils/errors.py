"""
Custom exception classes for zsys ecosystem.

Provides structured error handling across all projects.
"""

try:
    from zsys._core import format_exc_html as _c_format_exc_html, C_AVAILABLE as _C
except ImportError:
    _C = False
    _c_format_exc_html = None


class BaseException(Exception):
    """Base exception for all zsys errors."""
    
    def __init__(self, message: str, details: dict = None):
        """Initialize error.
        
        Args:
            message: Error message
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        """String representation."""
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


class ConfigError(BaseException):
    """Configuration-related errors."""
    pass


class DatabaseError(BaseException):
    """Database operation errors."""
    pass


class APIError(BaseException):
    """API/HTTP request errors."""
    
    def __init__(self, message: str, status_code: int = None, details: dict = None):
        """Initialize API error.
        
        Args:
            message: Error message
            status_code: HTTP status code
            details: Additional details
        """
        super().__init__(message, details)
        self.status_code = status_code


class BotError(BaseException):
    """Bot operation errors."""
    pass


class AuthenticationError(BaseException):
    """Authentication/authorization errors."""
    pass


class ValidationError(BaseException):
    """Data validation errors."""
    
    def __init__(self, message: str, field: str = None, details: dict = None):
        """Initialize validation error.
        
        Args:
            message: Error message
            field: Field that failed validation
            details: Additional details
        """
        super().__init__(message, details)
        self.field = field


class NetworkError(BaseException):
    """Network/connectivity errors."""
    pass


class ModuleError(BaseException):
    """Module loading/execution errors."""
    pass


class FileError(BaseException):
    """File operation errors."""
    pass


class LicenseError(BaseException):
    """Licensing-related errors."""
    pass


class SessionError(BaseException):
    """Session-related errors."""
    pass


# =============================================================================
# MEDIA/CDN ERRORS (from qp-media)
# =============================================================================

class MediaError(BaseException):
    """Base media operation error."""
    pass


class MediaNotFoundError(MediaError):
    """Media not found."""
    def __init__(self, media_id: str, details: dict = None):
        super().__init__(f"Media not found: {media_id}", details)
        self.media_id = media_id


class MediaExistsError(MediaError):
    """Media already exists (duplicate hash)."""
    def __init__(self, hash_value: str, details: dict = None):
        super().__init__(f"Media with hash {hash_value} already exists", details)
        self.hash_value = hash_value


class InvalidMediaTypeError(MediaError):
    """Invalid media type."""
    def __init__(self, media_type: str, details: dict = None):
        super().__init__(f"Invalid media type: {media_type}", details)
        self.media_type = media_type


class StorageError(BaseException):
    """Storage operation error."""
    pass


class PermissionDeniedError(BaseException):
    """Permission denied."""
    def __init__(self, action: str, details: dict = None):
        super().__init__(f"Permission denied: {action}", details)
        self.action = action


# =============================================================================
# ERROR FORMATTING UTILITIES
# =============================================================================

def handle_error(error: Exception, default_message: str = "An error occurred") -> str:
    """Format error for display to user.
    
    Args:
        error: Exception to format
        default_message: Default message if error is generic
        
    Returns:
        Formatted error message
    """
    if isinstance(error, BaseException):
        msg = f"<b>❌ {error.__class__.__name__}</b>\n\n{error.message}"
        if error.details:
            msg += f"\n\n<b>Details:</b>\n"
            for key, value in error.details.items():
                msg += f"• {key}: {value}\n"
        return msg
    
    return f"<b>❌ Error</b>\n\n{default_message}\n\n<code>{str(error)}</code>"


def format_exc(
    e: Exception,
    suffix: str = "",
    max_length: int = 4000,
    include_cause: bool = True,
    escape_html: bool = True,
    show_traceback: bool = False
) -> str:
    """
    Format exception for display (HTML).
    
    Args:
        e: Exception to format
        suffix: Additional text to append
        max_length: Maximum message length (truncated if exceeded)
        include_cause: Include __cause__ if available
        escape_html: Escape HTML special characters
        show_traceback: Print traceback to console
        
    Returns:
        Formatted error message in HTML
    """
    import traceback as tb
    from html import escape as html_escape
    
    if show_traceback:
        tb.print_exc()

    # Check for Telegram RPC errors
    try:
        from pyrogram import errors as pyrogram_errors
        if isinstance(e, pyrogram_errors.RPCError):
            return _format_telegram_rpc_error(e)
    except ImportError:
        pass

    error_type = e.__class__.__name__
    error_text = str(e) or "No error message"

    cause_type = cause_text = ""
    if include_cause and e.__cause__:
        cause_type = e.__cause__.__class__.__name__
        cause_text = str(e.__cause__)

    if _C and escape_html:
        return _c_format_exc_html(
            error_type, error_text,
            cause_type, cause_text,
            suffix, max_length,
        )

    # Python fallback (or escape_html=False path)
    def _escape(text: str) -> str:
        from html import escape as _he
        return _he(text) if escape_html else text

    error_msg = f"<b>Error!</b>\n<code>{_escape(error_type)}: {_escape(error_text)}</code>"
    if cause_type:
        error_msg += f"\n<b>Caused by:</b> <code>{_escape(cause_type)}: {_escape(cause_text)}</code>"
    if suffix:
        error_msg += f"\n\n<b>{_escape(suffix)}</b>"
    if max_length and len(error_msg) > max_length:
        error_msg = error_msg[:max_length - 3] + "..."
    return error_msg


def _format_telegram_rpc_error(e) -> str:
    """Format Telegram API RPC error."""
    error_details = {
        "code": getattr(e, "CODE", "UNKNOWN"),
        "id": getattr(e, "ID", getattr(e, "NAME", "UNKNOWN")),
        "message": getattr(e, "MESSAGE", "Unknown error").format(value=getattr(e, "value", "")),
        "description": getattr(e, "description", "")
    }
    
    return (
        "<b>Telegram API Error!</b>\n"
        f"<code>"
        f"[{error_details['code']} {error_details['id']}] - {error_details['message']}\n"
        f"{error_details['description']}"
        f"</code>"
    )


def print_exc(
    e: Exception,
    context: str = None,
    show_traceback: bool = True
) -> None:
    """
    Print exception to console with optional context.
    
    Args:
        e: Exception to print
        context: Additional context description
        show_traceback: Whether to print full traceback
    """
    import traceback
    import sys
    
    if context:
        print(f"Error in {context}:", file=sys.stderr)
    else:
        print("Error occurred:", file=sys.stderr)
    
    if show_traceback:
        traceback.print_exc()
    else:
        print(f"{e.__class__.__name__}: {str(e)}", file=sys.stderr)
    
    if e.__cause__:
        print(f"Caused by: {e.__cause__.__class__.__name__}: {str(e.__cause__)}", file=sys.stderr)
