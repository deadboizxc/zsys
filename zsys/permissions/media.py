"""Permission checks for media operations."""
from typing import TYPE_CHECKING

from zsys.core.exceptions import PermissionDeniedError

if TYPE_CHECKING:
    from zsys.data.orm import MediaFile, User


def can_delete_media(user: "User", media: "MediaFile") -> bool:
    """Check if user can delete media."""
    return bool(media.owner_id == user.id)


def can_update_media(user: "User", media: "MediaFile") -> bool:
    """Check if user can update media."""
    return bool(media.owner_id == user.id)


def require_delete_permission(user: "User", media: "MediaFile") -> None:
    """Raise if user cannot delete media."""
    if not can_delete_media(user, media):
        raise PermissionDeniedError("delete")


def require_update_permission(user: "User", media: "MediaFile") -> None:
    """Raise if user cannot update media."""
    if not can_update_media(user, media):
        raise PermissionDeniedError("update")
