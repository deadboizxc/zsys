"""
Base Media Service - Abstract interface for media/CDN services.

Inherits from BaseConfig and adds media-specific functionality:
- File upload/download
- Media processing (resize, convert)
- Storage management
- CDN integration

⭐ UNIFIED CONFIG: MediaConfig now inherits from BaseConfig
"""

from abc import abstractmethod
from dataclasses import dataclass, field
from typing import (
    Any, BinaryIO, Dict, List, Optional,
    TypeVar, Union
)
from enum import Enum, auto
from pathlib import Path
import mimetypes
import sys

from ..config import BaseConfig, Field
from .base import BaseClient, ClientState, ClientError

__all__ = [
    'BaseMediaService',
    'MediaConfig',
    'MediaType',
    'MediaFile',
    'StorageBackend',
    'UploadResult',
    'MediaError',
    'StorageError',
    'QuotaExceededError',
]


class MediaType(Enum):
    """Media file types."""
    IMAGE = auto()
    VIDEO = auto()
    AUDIO = auto()
    DOCUMENT = auto()
    ARCHIVE = auto()
    UNKNOWN = auto()
    
    @classmethod
    def from_mime(cls, mime_type: str) -> "MediaType":
        """Detect type from MIME type."""
        if not mime_type:
            return cls.UNKNOWN
        
        main_type = mime_type.split("/")[0]
        
        if main_type == "image":
            return cls.IMAGE
        elif main_type == "video":
            return cls.VIDEO
        elif main_type == "audio":
            return cls.AUDIO
        elif mime_type in ("application/zip", "application/x-rar", "application/x-7z-compressed"):
            return cls.ARCHIVE
        else:
            return cls.DOCUMENT
    
    @classmethod
    def from_extension(cls, ext: str) -> "MediaType":
        """Detect type from file extension."""
        ext = ext.lower().lstrip(".")
        
        image_exts = {"jpg", "jpeg", "png", "gif", "webp", "bmp", "svg", "ico"}
        video_exts = {"mp4", "avi", "mkv", "webm", "mov", "wmv", "flv"}
        audio_exts = {"mp3", "wav", "ogg", "flac", "m4a", "aac", "wma"}
        archive_exts = {"zip", "rar", "7z", "tar", "gz", "bz2"}
        
        if ext in image_exts:
            return cls.IMAGE
        elif ext in video_exts:
            return cls.VIDEO
        elif ext in audio_exts:
            return cls.AUDIO
        elif ext in archive_exts:
            return cls.ARCHIVE
        else:
            return cls.DOCUMENT


class StorageBackend(Enum):
    """Storage backend types."""
    LOCAL = auto()       # Local filesystem
    S3 = auto()          # Amazon S3 / compatible
    CLOUDFLARE = auto()  # Cloudflare R2
    GCS = auto()         # Google Cloud Storage
    TELEGRAM = auto()    # Telegram as storage
    MEMORY = auto()      # In-memory (testing)


class MediaError(Exception):
    """Media processing error."""
    pass


class StorageError(MediaError):
    """Storage operation error."""
    pass


class QuotaExceededError(StorageError):
    """Storage quota exceeded."""
    def __init__(self, used: int, limit: int):
        message = f"Storage quota exceeded: {used}/{limit} bytes"
        super().__init__(message)
        self.used = used
        self.limit = limit


class MediaConfig(BaseConfig):
    """
    Media service configuration - extends universal BaseConfig.
    
    Now uses Pydantic BaseConfig instead of dataclass.
    Inherits common fields: app_name, debug, log_level
    """
    
    # === Storage ===
    storage_backend: str = Field(
        default="LOCAL",
        description="Storage backend (LOCAL, S3, CLOUDFLARE, etc.)"
    )
    storage_path: str = Field(
        default="./storage",
        description="Path for local storage"
    )
    
    # === S3-compatible settings ===
    s3_endpoint: str = Field(
        default="",
        description="S3 endpoint URL"
    )
    s3_bucket: str = Field(
        default="",
        description="S3 bucket name"
    )
    s3_access_key: str = Field(
        default="",
        description="S3 access key"
    )
    s3_secret_key: str = Field(
        default="",
        description="S3 secret key"
    )
    s3_region: str = Field(
        default="auto",
        description="S3 region"
    )
    
    # === CDN ===
    cdn_url: str = Field(
        default="",
        description="Public CDN URL"
    )
    
    # === Limits ===
    max_file_size: int = Field(
        default=50 * 1024 * 1024,
        description="Maximum file size (bytes)"
    )
    max_total_storage: int = Field(
        default=10 * 1024 * 1024 * 1024,
        description="Maximum total storage (bytes)"
    )
    allowed_types: List[str] = Field(
        default_factory=lambda: ["image/*", "video/*", "audio/*"],
        description="Allowed MIME types"
    )
    
    # === Processing ===
    auto_convert: bool = Field(
        default=True,
        description="Auto-convert to web formats"
    )
    generate_thumbnails: bool = Field(
        default=True,
        description="Generate thumbnails"
    )
    
    # === Image processing ===
    max_image_dimension: int = Field(
        default=4096,
        description="Maximum image dimension (pixels)"
    )
    jpeg_quality: int = Field(
        default=85,
        description="JPEG quality (1-100)"
    )
    webp_quality: int = Field(
        default=80,
        description="WebP quality (1-100)"
    )
    
    # === Video processing ===
    video_codec: str = Field(
        default="h264",
        description="Video codec"
    )
    audio_codec: str = Field(
        default="aac",
        description="Audio codec"
    )
    
    class Config:
        env_prefix = "MEDIA_"


class MediaFile:
    """Media file representation."""
    
    def __init__(
        self,
        id: str,
        filename: str,
        size: int,
        mime_type: str,
        media_type: MediaType,
        url: str = "",
        path: str = "",
        width: int = 0,
        height: int = 0,
        duration: float = 0,
        md5: str = "",
        sha256: str = "",
        created_at: int = 0,
        updated_at: int = 0,
        thumbnail_url: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = id
        self.filename = filename
        self.size = size
        self.mime_type = mime_type
        self.media_type = media_type
        self.url = url
        self.path = path
        self.width = width
        self.height = height
        self.duration = duration
        self.md5 = md5
        self.sha256 = sha256
        self.created_at = created_at
        self.updated_at = updated_at
        self.thumbnail_url = thumbnail_url
        self.metadata = metadata or {}
    
    @property
    def extension(self) -> str:
        """Get file extension."""
        if "." in self.filename:
            return self.filename.rsplit(".", 1)[-1].lower()
        return ""
    
    @property
    def is_image(self) -> bool:
        return self.media_type == MediaType.IMAGE
    
    @property
    def is_video(self) -> bool:
        return self.media_type == MediaType.VIDEO
    
    @property
    def is_audio(self) -> bool:
        return self.media_type == MediaType.AUDIO


@dataclass
class UploadResult:
    """Result of upload operation."""
    success: bool
    file: Optional[MediaFile] = None
    error: Optional[str] = None
    
    # Multiple files
    files: List[MediaFile] = field(default_factory=list)
    
    @property
    def url(self) -> str:
        """Get URL of uploaded file."""
        if self.file:
            return self.file.url
        return ""


class BaseMediaService(BaseClient[MediaConfig]):
    """
    Abstract base class for media/CDN services.
    
    Provides:
    - File upload/download
    - Media type detection
    - Storage management
    - CDN URL generation
    
    Subclasses must implement:
    - _do_start(): Initialize storage connection
    - _do_stop(): Cleanup
    - _health_check(): Check storage availability
    - upload(): Upload file
    - download(): Download file
    - delete(): Delete file
    - get_file(): Get file info
    
    Example:
        class S3MediaService(BaseMediaService):
            def __init__(self, config: MediaConfig):
                super().__init__(config)
                self._s3 = boto3.client(...)
            
            async def upload(self, data, filename):
                key = self._generate_key(filename)
                await self._s3.put_object(...)
                return UploadResult(
                    success=True,
                    file=MediaFile(id=key, ...)
                )
    """
    
    def __init__(self, config: MediaConfig = None):
        super().__init__(config or MediaConfig())
        
        # Storage stats
        self._total_files: int = 0
        self._total_size: int = 0
    
    def _default_config(self) -> MediaConfig:
        return MediaConfig()
    
    # =========================================================================
    # ABSTRACT METHODS
    # =========================================================================
    
    @abstractmethod
    async def _do_start(self) -> None:
        """Initialize storage connection."""
        pass
    
    @abstractmethod
    async def _do_stop(self) -> None:
        """Cleanup storage connection."""
        pass
    
    @abstractmethod
    async def _health_check(self) -> bool:
        """Check storage availability."""
        pass
    
    # =========================================================================
    # ABSTRACT: FILE OPERATIONS
    # =========================================================================
    
    @abstractmethod
    async def upload(
        self,
        data: Union[bytes, BinaryIO, str, Path],
        filename: str = None,
        *,
        folder: str = "",
        public: bool = True,
        metadata: Dict[str, Any] = None,
        **kwargs
    ) -> UploadResult:
        """
        Upload file to storage.
        
        Args:
            data: File data (bytes, file object, or path)
            filename: Filename (auto-detected if None)
            folder: Subfolder in storage
            public: Make file publicly accessible
            metadata: Additional metadata
            
        Returns:
            UploadResult with file info
            
        Raises:
            QuotaExceededError: Storage limit reached
            MediaError: Upload failed
        """
        pass
    
    @abstractmethod
    async def download(
        self,
        file_id: str,
        destination: Union[str, Path, BinaryIO] = None,
        **kwargs
    ) -> Union[bytes, str]:
        """
        Download file from storage.
        
        Args:
            file_id: File ID or path
            destination: Where to save (None = return bytes)
            
        Returns:
            File bytes or path to saved file
        """
        pass
    
    @abstractmethod
    async def delete(
        self,
        file_id: str,
        **kwargs
    ) -> bool:
        """
        Delete file from storage.
        
        Args:
            file_id: File ID or path
            
        Returns:
            True if deleted
        """
        pass
    
    @abstractmethod
    async def get_file(
        self,
        file_id: str,
    ) -> Optional[MediaFile]:
        """
        Get file info.
        
        Args:
            file_id: File ID or path
            
        Returns:
            MediaFile or None if not found
        """
        pass
    
    @abstractmethod
    async def list_files(
        self,
        folder: str = "",
        *,
        limit: int = 100,
        offset: int = 0,
        media_type: MediaType = None,
    ) -> List[MediaFile]:
        """
        List files in storage.
        
        Args:
            folder: Folder to list
            limit: Max files to return
            offset: Pagination offset
            media_type: Filter by type
            
        Returns:
            List of MediaFile objects
        """
        pass
    
    # =========================================================================
    # ABSTRACT: URL GENERATION
    # =========================================================================
    
    @abstractmethod
    def get_url(
        self,
        file_id: str,
        *,
        expires: int = None,  # seconds
        **kwargs
    ) -> str:
        """
        Get public URL for file.
        
        Args:
            file_id: File ID or path
            expires: URL expiration (presigned URL)
            
        Returns:
            Public URL
        """
        pass
    
    # =========================================================================
    # OPTIONAL: PROCESSING
    # =========================================================================
    
    async def create_thumbnail(
        self,
        file_id: str,
        size: tuple = None,
    ) -> Optional[str]:
        """
        Create thumbnail for image/video.
        
        Override in subclass for actual implementation.
        
        Args:
            file_id: Source file ID
            size: Thumbnail size (width, height)
            
        Returns:
            Thumbnail URL or None
        """
        # Default: not implemented
        return None
    
    async def convert(
        self,
        file_id: str,
        target_format: str,
        **kwargs
    ) -> Optional[UploadResult]:
        """
        Convert file to different format.
        
        Override in subclass for actual implementation.
        
        Args:
            file_id: Source file ID
            target_format: Target format (e.g., "webp", "mp4")
            
        Returns:
            UploadResult with converted file
        """
        # Default: not implemented
        return None
    
    async def resize_image(
        self,
        file_id: str,
        width: int = None,
        height: int = None,
        **kwargs
    ) -> Optional[UploadResult]:
        """
        Resize image.
        
        Override in subclass for actual implementation.
        """
        return None
    
    # =========================================================================
    # UTILITY
    # =========================================================================
    
    def detect_media_type(
        self,
        filename: str = None,
        mime_type: str = None,
    ) -> MediaType:
        """Detect media type from filename or MIME type."""
        if mime_type:
            return MediaType.from_mime(mime_type)
        
        if filename:
            # Try to get MIME from filename
            guessed_mime, _ = mimetypes.guess_type(filename)
            if guessed_mime:
                return MediaType.from_mime(guessed_mime)
            
            # Fallback to extension
            ext = filename.rsplit(".", 1)[-1] if "." in filename else ""
            return MediaType.from_extension(ext)
        
        return MediaType.UNKNOWN
    
    def is_allowed_type(self, mime_type: str) -> bool:
        """Check if MIME type is allowed."""
        if not self._config.allowed_types:
            return True
        
        for pattern in self._config.allowed_types:
            if pattern == "*/*":
                return True
            
            if pattern.endswith("/*"):
                # Wildcard: "image/*"
                main_type = pattern[:-2]
                if mime_type.startswith(main_type + "/"):
                    return True
            elif mime_type == pattern:
                return True
        
        return False
    
    def validate_file_size(self, size: int) -> bool:
        """Check if file size is within limits."""
        return size <= self._config.max_file_size
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        return {
            "total_files": self._total_files,
            "total_size": self._total_size,
            "max_size": self._config.max_total_storage,
            "used_percent": (self._total_size / self._config.max_total_storage * 100) 
                           if self._config.max_total_storage > 0 else 0,
        }
    
    # =========================================================================
    # PROPERTIES
    # =========================================================================
    
    @property
    def cdn_url(self) -> str:
        """Get CDN base URL."""
        return self._config.cdn_url
    
    @property
    def storage_backend(self) -> StorageBackend:
        """Get storage backend type."""
        return self._config.storage_backend
    
    @property
    def max_file_size(self) -> int:
        """Get max file size limit."""
        return self._config.max_file_size
