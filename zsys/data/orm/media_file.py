"""BaseMediaFile model - stored media file entity."""

from sqlalchemy import Column, String, Integer, ForeignKey

from .base import BaseModel


class BaseMediaFile(BaseModel):
    """
    Base MediaFile model - represents a stored media file.
    
    Used for CDN, media storage, stickers, GIFs, etc.
    
    Attributes:
        filename: Original filename
        file_hash: SHA-256 hash of file content (for deduplication)
        mime_type: MIME type (image/png, video/mp4, etc.)
        size: File size in bytes
        url: Public URL to access the file
        storage_path: Path in the storage backend
        media_type: Logical type ('file', 'image', 'video', 'audio', 'sticker', 'gif')
        owner_id: User who uploaded the file (optional)
    """
    __tablename__ = "media_files"
    
    filename = Column(String(255), nullable=False)
    file_hash = Column(String(64), unique=True, nullable=True, index=True)
    mime_type = Column(String(100), nullable=False)
    size = Column(Integer, nullable=False)  # bytes
    url = Column(String(500), nullable=False)
    storage_path = Column(String(500), nullable=True)
    media_type = Column(String(50), default="file", index=True)  # file, image, video, audio, sticker, gif
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    @property
    def is_image(self) -> bool:
        return self.media_type == "image" or self.mime_type.startswith("image/")
    
    @property
    def is_video(self) -> bool:
        return self.media_type == "video" or self.mime_type.startswith("video/")
    
    @property
    def is_audio(self) -> bool:
        return self.media_type == "audio" or self.mime_type.startswith("audio/")
    
    def __repr__(self) -> str:
        return f"<BaseMediaFile(id={self.id}, filename={self.filename}, type={self.media_type})>"


# Backward compatible alias
MediaFile = BaseMediaFile

__all__ = ['BaseMediaFile', 'MediaFile']
