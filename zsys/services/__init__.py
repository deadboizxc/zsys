"""
Core services - media handling and storage implementations.

Warning: Do not import bot implementations here (like Instagram, Discord bots).
Bot implementations must be placed outside zsys/ directory and inherit from
base classes in zsys.core.messaging.

Only core utility services (MediaService, StorageService) are exported here.
"""


# Import media services (lazy, because aiofiles may not be installed)
def __getattr__(name):
    if name in (
        "MediaService",
        "StorageService",
        "MediaRepository",
        "GiphyService",
        "detect_media_type_from_mime",
    ):
        from zsys.services.media_service import (
            MediaService,
            StorageService,
            MediaRepository,
            GiphyService,
            detect_media_type_from_mime,
        )

        mapping = {
            "MediaService": MediaService,
            "StorageService": StorageService,
            "MediaRepository": MediaRepository,
            "GiphyService": GiphyService,
            "detect_media_type_from_mime": detect_media_type_from_mime,
        }
        if name in mapping:
            return mapping[name]

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = [
    # Media service (from media_service.py)
    # Note: Import specific classes as needed
]
