"""Core business logic services."""

import asyncio
import json
import logging
import mimetypes
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import UUID, uuid4

import aiofiles
import aiohttp

from zsys.core.domain.crypto import compute_file_hash
from zsys.core.exceptions import (
    MediaNotFoundError,
    MediaExistsError,
    InvalidMediaTypeError,
    StorageError,
    APIError,
)
from zsys.data.orm import MediaFile, User
from zsys.permissions import require_delete_permission, require_update_permission

logger = logging.getLogger(__name__)


def detect_media_type_from_mime(mime_type: str, filename: str) -> str:
    """Detect media type from mime type and filename."""
    mime_lower = mime_type.lower()
    fname_lower = filename.lower()

    # GIF
    if "gif" in mime_lower or fname_lower.endswith(".gif"):
        return "gif"
    # Stickers (Telegram formats)
    elif fname_lower.endswith((".tgs", ".webp")) or "tgsticker" in mime_lower:
        return "sticker"
    # Video
    elif "video" in mime_lower or fname_lower.endswith(
        (".mp4", ".webm", ".mov", ".avi", ".mkv")
    ):
        return "video"
    # Audio
    elif "audio" in mime_lower or fname_lower.endswith(
        (".mp3", ".ogg", ".wav", ".flac", ".m4a", ".opus", ".aac")
    ):
        return "audio"
    # Image
    elif "image" in mime_lower or fname_lower.endswith(
        (".png", ".jpg", ".jpeg", ".bmp", ".tiff")
    ):
        return "image"
    # Everything else is a document
    else:
        return "document"


class MediaRepository:
    """In-memory + file-based media repository (legacy - use SQLAlchemy)."""

    def __init__(self, db_path: Path):
        self._db_path = db_path
        self._media: dict[UUID, dict] = {}
        self._hash_index: dict[str, UUID] = {}
        self._lock = asyncio.Lock()

    async def load(self) -> None:
        """Load database from file."""
        if not self._db_path.exists():
            return
        try:
            async with aiofiles.open(self._db_path, "r") as f:
                data = json.loads(await f.read())
            for item in data:
                media_id = UUID(item["id"])
                self._media[media_id] = item
                self._hash_index[item["hash"]] = media_id
            logger.info(f"Loaded {len(self._media)} media items")
        except Exception as e:
            logger.error(f"Failed to load media database: {e}")

    async def save(self) -> None:
        """Save database to file."""
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        data = list(self._media.values())
        async with aiofiles.open(self._db_path, "w") as f:
            await f.write(json.dumps(data, indent=2, default=str))

    async def add(self, media_data: dict) -> None:
        """Add media to repository."""
        async with self._lock:
            if media_data["hash"] in self._hash_index:
                raise MediaExistsError(media_data["hash"])
            media_id = UUID(media_data["id"])
            self._media[media_id] = media_data
            self._hash_index[media_data["hash"]] = media_id
            await self.save()

    async def get(self, media_id: UUID) -> dict:
        """Get media by ID."""
        if media_id not in self._media:
            raise MediaNotFoundError(str(media_id))
        return self._media[media_id]

    async def get_by_hash(self, hash_value: str) -> Optional[dict]:
        """Get media by hash."""
        if hash_value in self._hash_index:
            return self._media[self._hash_index[hash_value]]
        return None

    async def delete(self, media_id: UUID) -> None:
        """Delete media from repository."""
        async with self._lock:
            if media_id not in self._media:
                raise MediaNotFoundError(str(media_id))
            media = self._media[media_id]
            del self._hash_index[media["hash"]]
            del self._media[media_id]
            await self.save()


class StorageService:
    """File storage service."""

    def __init__(self, storage_dir: Path):
        self._storage_dir = storage_dir
        self._storage_dir.mkdir(parents=True, exist_ok=True)

    def get_path(self, media_id: UUID, extension: str) -> Path:
        """Get file path for media."""
        return self._storage_dir / f"{media_id}.{extension}"

    async def save(self, media_id: UUID, extension: str, data: bytes) -> Path:
        """Save file to storage."""
        path = self.get_path(media_id, extension)
        try:
            async with aiofiles.open(path, "wb") as f:
                await f.write(data)
            return path
        except IOError as e:
            raise StorageError(f"Failed to save file: {e}")

    async def delete(self, media_id: UUID, extension: str) -> None:
        """Delete file from storage."""
        path = self.get_path(media_id, extension)
        try:
            if path.exists():
                path.unlink()
        except IOError as e:
            raise StorageError(f"Failed to delete file: {e}")

    async def read(self, media_id: UUID, extension: str) -> bytes:
        """Read file from storage."""
        path = self.get_path(media_id, extension)
        if not path.exists():
            raise StorageError(f"File not found: {path}")
        async with aiofiles.open(path, "rb") as f:
            return await f.read()


class GiphyService:
    """Giphy GIF API integration (free tier)."""

    def __init__(self, api_key: str):
        self._api_key = api_key
        self._base_url = "https://api.giphy.com/v1/gifs"

    async def get_gif(self, giphy_id: str) -> tuple[bytes, str]:
        """Fetch GIF from Giphy by ID. Returns (data, url)."""
        if not self._api_key:
            raise APIError("Giphy API key not configured")

        async with aiohttp.ClientSession() as session:
            # Get GIF info
            url = f"{self._base_url}/{giphy_id}"
            params = {"api_key": self._api_key}

            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    raise APIError(f"Failed to fetch GIF info: {resp.status}")
                data = await resp.json()

            if not data.get("data"):
                raise APIError(f"GIF not found: {giphy_id}")

            result = data["data"]
            gif_url = result["images"]["original"]["url"]

            # Download GIF
            async with session.get(gif_url) as resp:
                if resp.status != 200:
                    raise APIError(f"Failed to download GIF: {resp.status}")
                gif_data = await resp.read()

            return gif_data, gif_url

    async def search(self, query: str, limit: int = 10) -> list[dict]:
        """Search GIFs on Giphy."""
        if not self._api_key:
            return []

        async with aiohttp.ClientSession() as session:
            url = f"{self._base_url}/search"
            params = {"api_key": self._api_key, "q": query, "limit": limit}

            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()

            return [
                {
                    "id": g["id"],
                    "url": g["images"]["original"]["url"],
                    "title": g.get("title", ""),
                }
                for g in data.get("data", [])
            ]


class MediaService:
    """Main media business logic service."""

    def __init__(
        self,
        repository: MediaRepository,
        storage: StorageService,
        giphy: GiphyService,
        base_url: str,
    ):
        self._repo = repository
        self._storage = storage
        self._giphy = giphy
        self._base_url = base_url.rstrip("/")

    async def initialize(self) -> None:
        """Initialize service (load database)."""
        await self._repo.load()

    def _build_url(self, media_id: UUID, extension: str) -> str:
        """Build public CDN URL for media."""
        return f"{self._base_url}/cdn/{media_id}.{extension}"

    async def add(
        self,
        file_data: bytes,
        filename: str,
        mime_type: str,
        tags: list[str],
        owner_id: str,
    ) -> dict:
        """Add new media from uploaded file."""
        # Compute hash and check for duplicates
        file_hash = compute_file_hash(file_data)
        existing = await self._repo.get_by_hash(file_hash)
        if existing:
            raise MediaExistsError(file_hash)

        # Detect type
        media_type = detect_media_type_from_mime(mime_type, filename)

        # Generate ID and extension
        media_id = uuid4()
        extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"

        # Save file
        await self._storage.save(media_id, extension, file_data)

        # Create media record
        media = {
            "id": str(media_id),
            "type": media_type,
            "source": "upload",
            "url": self._build_url(media_id, extension),
            "tags": tags,
            "owner_id": owner_id,
            "hash": file_hash,
            "filename": filename,
            "mime_type": mime_type,
            "size": len(file_data),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        await self._repo.add(media)
        logger.info(f"Added media: {media_id}")
        return media

    async def import_from_giphy(
        self,
        giphy_id: str,
        tags: list[str],
        owner_id: str,
    ) -> dict:
        """Import GIF from Giphy."""
        gif_data, original_url = await self._giphy.get_gif(giphy_id)

        # Check for duplicates
        file_hash = compute_file_hash(gif_data)
        existing = await self._repo.get_by_hash(file_hash)
        if existing:
            raise MediaExistsError(file_hash)

        # Generate ID
        media_id = uuid4()
        extension = "gif"

        # Save file
        await self._storage.save(media_id, extension, gif_data)

        # Create media record
        media = {
            "id": str(media_id),
            "type": "gif",
            "source": "giphy",
            "url": self._build_url(media_id, extension),
            "tags": tags,
            "owner_id": owner_id,
            "hash": file_hash,
            "filename": f"{giphy_id}.gif",
            "mime_type": "image/gif",
            "size": len(gif_data),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        await self._repo.add(media)
        logger.info(f"Imported from Giphy: {media_id}")
        return media

    async def get(self, media_id: str | UUID) -> dict:
        """Get media by ID."""
        if isinstance(media_id, str):
            media_id = UUID(media_id)
        return await self._repo.get(media_id)

    async def import_from_url(
        self,
        url: str,
        tags: list[str],
        owner_id: str,
    ) -> dict:
        """Import media from external URL."""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    raise StorageError(f"Failed to fetch URL: {resp.status}")
                file_data = await resp.read()
                content_type = resp.headers.get(
                    "Content-Type", "application/octet-stream"
                )

        # Get filename from URL
        filename = url.split("/")[-1].split("?")[0] or "media"

        # Check for duplicates
        file_hash = compute_file_hash(file_data)
        existing = await self._repo.get_by_hash(file_hash)
        if existing:
            raise MediaExistsError(file_hash)

        # Detect type
        media_type = detect_media_type_from_mime(content_type, filename)

        # Generate ID and extension
        media_id = uuid4()
        extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"

        # Save file
        await self._storage.save(media_id, extension, file_data)

        # Create media record
        media = {
            "id": str(media_id),
            "type": media_type,
            "source": "external",
            "url": self._build_url(media_id, extension),
            "tags": tags,
            "owner_id": owner_id,
            "hash": file_hash,
            "filename": filename,
            "mime_type": content_type,
            "size": len(file_data),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        await self._repo.add(media)
        logger.info(f"Imported from URL: {media_id}")
        return media

    async def delete(self, media_id: str | UUID, user: User) -> None:
        """Delete media."""
        if isinstance(media_id, str):
            media_id = UUID(media_id)

        media_data = await self._repo.get(media_id)
        # TODO: Add permission check when User model is fully integrated

        # Delete file
        extension = (
            media_data["filename"].rsplit(".", 1)[-1].lower()
            if "." in media_data["filename"]
            else "bin"
        )
        await self._storage.delete(media_id, extension)

        # Delete from repository
        await self._repo.delete(media_id)
        logger.info(f"Deleted media: {media_id}")
