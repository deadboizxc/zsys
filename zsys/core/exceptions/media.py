"""Media-related exceptions."""

from .base import BaseException


class MediaError(BaseException):
    """Base class for media-related errors."""
    pass


class MediaNotFoundError(MediaError):
    """Media file not found in database."""
    
    def __init__(self, media_id: str, code: str | None = None):
        message = f"Media not found: {media_id}"
        super().__init__(message, code)
        self.media_id = media_id


class MediaExistsError(MediaError):
    """Media already exists (duplicate hash)."""
    
    def __init__(self, hash_value: str, code: str | None = None):
        message = f"Media with hash {hash_value} already exists"
        super().__init__(message, code)
        self.hash = hash_value


class InvalidMediaTypeError(MediaError):
    """Unsupported/invalid media type."""
    
    def __init__(self, media_type: str, code: str | None = None):
        message = f"Invalid media type: {media_type}"
        super().__init__(message, code)
        self.media_type = media_type
