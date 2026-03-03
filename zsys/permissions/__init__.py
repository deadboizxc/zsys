"""Permission checks and authorization."""

from .media import (
    can_delete_media,
    can_update_media,
    require_delete_permission,
    require_update_permission,
)

__all__ = [
    "can_delete_media",
    "can_update_media",
    "require_delete_permission",
    "require_update_permission",
]
