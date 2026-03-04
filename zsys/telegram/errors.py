"""TDLib error hierarchy — mirrors Pyrogram/Telethon exception names.

Raised automatically by TdlibClient when a pending callback returns
``{"@type": "error", "code": N, "message": "..."}``.
"""
# RU: Иерархия ошибок TDLib. Аналог Pyrogram исключений.

from __future__ import annotations

import re


class TdlibError(Exception):
    """Base TDLib error."""

    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")


class FloodWait(TdlibError):
    """Too many requests — caller must wait ``seconds`` before retrying."""

    def __init__(self, seconds: int) -> None:
        self.seconds = seconds
        super().__init__(420, f"FLOOD_WAIT_{seconds}")


class MessageDeleteForbidden(TdlibError):
    def __init__(self) -> None:
        super().__init__(403, "MESSAGE_DELETE_FORBIDDEN")


class MessageNotModified(TdlibError):
    def __init__(self) -> None:
        super().__init__(400, "MESSAGE_NOT_MODIFIED")


class ChatAdminRequired(TdlibError):
    def __init__(self) -> None:
        super().__init__(400, "CHAT_ADMIN_REQUIRED")


class UserNotParticipant(TdlibError):
    def __init__(self) -> None:
        super().__init__(400, "USER_NOT_PARTICIPANT")


class PeerIdInvalid(TdlibError):
    def __init__(self) -> None:
        super().__init__(400, "PEER_ID_INVALID")


class UserIsBlocked(TdlibError):
    def __init__(self) -> None:
        super().__init__(403, "USER_IS_BLOCKED")


class UserAdminInvalid(TdlibError):
    def __init__(self) -> None:
        super().__init__(400, "USER_ADMIN_INVALID")


class UsernameInvalid(TdlibError):
    def __init__(self) -> None:
        super().__init__(400, "USERNAME_INVALID")


class UsernameNotOccupied(TdlibError):
    def __init__(self) -> None:
        super().__init__(400, "USERNAME_NOT_OCCUPIED")


class BadRequest(TdlibError):
    def __init__(self, message: str = "BAD_REQUEST") -> None:
        super().__init__(400, message)


class Unauthorized(TdlibError):
    def __init__(self) -> None:
        super().__init__(401, "UNAUTHORIZED")


class Forbidden(TdlibError):
    def __init__(self, message: str = "FORBIDDEN") -> None:
        super().__init__(403, message)


class SessionPasswordNeeded(TdlibError):
    def __init__(self) -> None:
        super().__init__(401, "SESSION_PASSWORD_NEEDED")


class RPCError(TdlibError):
    """Generic TDLib RPC error not matching a specific subclass."""

    pass


def raise_for_error(code: int, message: str) -> None:
    """Parse TDLib error fields and raise the appropriate Python exception.

    Args:
        code:    TDLib error code.
        message: TDLib error message string.

    Raises:
        TdlibError subclass matching the error, or RPCError for unknown codes.
    """
    # RU: Разбираем ошибку TDLib и бросаем нужное исключение.
    msg_upper = message.upper()

    if code == 420 or "FLOOD" in msg_upper:
        m = re.search(r"(\d+)", message)
        raise FloodWait(int(m.group(1)) if m else 30)

    if "MESSAGE_DELETE_FORBIDDEN" in msg_upper or (
        code == 403 and "delete" in message.lower()
    ):
        raise MessageDeleteForbidden()

    if "MESSAGE_NOT_MODIFIED" in msg_upper:
        raise MessageNotModified()

    if "CHAT_ADMIN_REQUIRED" in msg_upper:
        raise ChatAdminRequired()

    if "USER_NOT_PARTICIPANT" in msg_upper:
        raise UserNotParticipant()

    if "PEER_ID_INVALID" in msg_upper:
        raise PeerIdInvalid()

    if "USER_IS_BLOCKED" in msg_upper or "USER_BLOCKED" in msg_upper:
        raise UserIsBlocked()

    raise RPCError(code, message)


__all__ = [
    "TdlibError",
    "FloodWait",
    "MessageDeleteForbidden",
    "MessageNotModified",
    "ChatAdminRequired",
    "UserNotParticipant",
    "PeerIdInvalid",
    "UserIsBlocked",
    "UserAdminInvalid",
    "UsernameInvalid",
    "UsernameNotOccupied",
    "BadRequest",
    "Unauthorized",
    "Forbidden",
    "SessionPasswordNeeded",
    "RPCError",
    "raise_for_error",
]
