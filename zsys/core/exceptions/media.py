"""ZSYS media exceptions — media-file and upload/download errors.

Raised by media service implementations when file operations, type
validation, or duplicate detection fail.
"""
# RU: Исключения медиафайлов — ошибки операций с медиаданными.
# RU: Возникают в медиасервисах при сбоях файловых операций или валидации типов.

from .base import BaseException


class MediaError(BaseException):
    """Base exception for all media-related errors.

    All more specific media exceptions inherit from this class, so callers
    can catch either the base or the specific subclass.

    Attributes:
        message: Human-readable error description.
        code: Optional error code string.
    """
    # RU: Базовое исключение для всех ошибок медиафайлов.
    pass


class MediaNotFoundError(MediaError):
    """Exception raised when a requested media file does not exist.

    Raised when a lookup by ID or path returns no result in the storage
    backend.

    Attributes:
        message: Human-readable error description including the media_id.
        media_id: The identifier that was not found.
    """
    # RU: Исключение при отсутствии медиафайла с заданным идентификатором.

    def __init__(self, media_id: str, code: str | None = None):
        """Initialise the error with the missing media identifier.

        Args:
            media_id: Identifier of the media file that was not found.
            code: Optional error code string.
        """
        # RU: Инициализировать с идентификатором отсутствующего медиафайла.
        message = f"Media not found: {media_id}"
        super().__init__(message, code)
        self.media_id = media_id


class MediaExistsError(MediaError):
    """Exception raised when a duplicate media file is detected.

    Raised when an upload's hash matches an already-stored file, preventing
    duplicate storage.

    Attributes:
        message: Human-readable error description including the hash.
        hash: Content hash of the duplicate file.
    """
    # RU: Исключение при обнаружении дубликата медиафайла по хешу.

    def __init__(self, hash_value: str, code: str | None = None):
        """Initialise the error with the duplicate content hash.

        Args:
            hash_value: Content hash of the file that already exists.
            code: Optional error code string.
        """
        # RU: Инициализировать с хешем существующего файла.
        message = f"Media with hash {hash_value} already exists"
        super().__init__(message, code)
        self.hash = hash_value


class InvalidMediaTypeError(MediaError):
    """Exception raised when a media file has an unsupported or forbidden type.

    Raised when MIME type checking rejects a file during upload validation.

    Attributes:
        message: Human-readable error description including the type.
        media_type: The MIME type string that was rejected.
    """
    # RU: Исключение при неподдерживаемом или запрещённом типе медиафайла.

    def __init__(self, media_type: str, code: str | None = None):
        """Initialise the error with the rejected MIME type.

        Args:
            media_type: The MIME type string that failed validation.
            code: Optional error code string.
        """
        # RU: Инициализировать с отклонённым MIME-типом.
        message = f"Invalid media type: {media_type}"
        super().__init__(message, code)
        self.media_type = media_type
