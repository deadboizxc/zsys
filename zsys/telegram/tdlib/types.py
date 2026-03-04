"""Python wrappers for libtg C types (tg_message_t, tg_user_t, tg_chat_t, etc.).

These objects wrap raw C pointers (valid ONLY inside a handler callback unless
the fields have already been copied out).  Calling accessor functions during
construction copies all fields eagerly, so the resulting Python objects are
safe to store.

Note:
    Message / User / Chat objects created inside a callback copy all fields
    immediately.  They are safe to store and pass around after the callback.
"""
# RU: Python обёртки для типов из tg.h.

from __future__ import annotations

import ctypes
from enum import IntEnum
from typing import List, Optional


# ── Media type enum ────────────────────────────────────────────────────────── #

class MediaType(IntEnum):
    """Maps to tg_media_type_t in tg.h."""
    NONE       = 0
    PHOTO      = 1
    VIDEO      = 2
    AUDIO      = 3
    DOCUMENT   = 4
    STICKER    = 5
    VOICE      = 6
    ANIMATION  = 7
    VIDEO_NOTE = 8
    LOCATION   = 9
    CONTACT    = 10
    POLL       = 11
    DICE       = 12
    VENUE      = 13


# ── User ───────────────────────────────────────────────────────────────────── #

class User:
    """Wrapper around tg_user_t*.

    Attributes:
        id:         Telegram user ID.
        first_name: First name.
        last_name:  Last name (may be empty).
        username:   Username without '@' (may be empty).
        phone:      Phone number (may be empty).
        is_bot:     True if the user is a bot.
        is_premium: True if the user has Telegram Premium.
    """

    __slots__ = ("id", "first_name", "last_name", "username", "phone",
                 "is_bot", "is_premium")

    def __init__(self, lib, ptr: int) -> None:
        # RU: Копируем поля пока указатель валиден.
        self.id:         int  = lib.tg_user_id(ptr)
        self.is_bot:     bool = bool(lib.tg_user_is_bot(ptr))
        self.is_premium: bool = False

        raw = lib.tg_user_first_name(ptr)
        self.first_name: str = raw.decode("utf-8", errors="replace") if raw else ""
        raw = lib.tg_user_last_name(ptr)
        self.last_name: str = raw.decode("utf-8", errors="replace") if raw else ""
        raw = lib.tg_user_username(ptr)
        self.username: str = raw.decode("utf-8", errors="replace") if raw else ""
        self.phone: str = ""

    @classmethod
    def _from_ptr(cls, lib, ptr: int) -> Optional["User"]:
        if not ptr:
            return None
        return cls(lib, ptr)

    def __repr__(self) -> str:
        return (f"<User id={self.id} username={self.username!r} "
                f"name={self.first_name!r}>")


# ── Chat ───────────────────────────────────────────────────────────────────── #

_CHAT_TYPE_NAMES = {0: "private", 1: "group", 2: "supergroup", 3: "channel"}


class Chat:
    """Wrapper around tg_chat_t*.

    Attributes:
        id:            Chat ID.
        title:         Chat title.
        username:      Public username (may be empty).
        type:          Chat type string: "private"|"group"|"supergroup"|"channel".
        members_count: Number of members (0 if unknown).
        linked_chat_id: ID of linked chat (e.g. discussion group for a channel).
        permissions:   TG_PERM_* bitmask.
        is_verified:   True if the chat is verified.
    """

    __slots__ = ("id", "title", "username", "type", "members_count",
                 "linked_chat_id", "permissions", "is_verified")

    def __init__(self, lib, ptr: int) -> None:
        self.id:             int  = lib.tg_chat_id(ptr)
        self.members_count:  int  = lib.tg_chat_members_count(ptr)
        self.linked_chat_id: int  = lib.tg_chat_linked_chat_id(ptr)
        self.permissions:    int  = lib.tg_chat_permissions(ptr)
        self.is_verified:    bool = False

        raw = lib.tg_chat_title(ptr)
        self.title: str = raw.decode("utf-8", errors="replace") if raw else ""
        raw = lib.tg_chat_username(ptr)
        self.username: str = raw.decode("utf-8", errors="replace") if raw else ""
        self.type: str = _CHAT_TYPE_NAMES.get(lib.tg_chat_type(ptr), "private")

    def __repr__(self) -> str:
        return f"<Chat id={self.id} title={self.title!r} type={self.type}>"


# ── ChatMember ─────────────────────────────────────────────────────────────── #

class ChatMember:
    """Wrapper around tg_chat_member_t*.

    Attributes:
        user:              The member's User object.
        status:            One of "member","administrator","creator",
                           "restricted","left","banned".
        is_admin:          True if administrator or creator.
        is_creator:        True if the chat creator.
        until_date:        Unix timestamp for restriction/ban end (0 = permanent).
        can_manage_chat:   Admin right.
        can_post_messages: Admin right.
        can_edit_messages: Admin right.
        can_delete_messages: Admin right.
        can_ban_users:     Admin right (can_restrict_members in TDLib).
        can_invite_users:  Admin right.
        can_pin_messages:  Admin right.
        can_promote_members: Admin right.
        can_change_info:   Admin right.
    """

    __slots__ = (
        "user", "status", "is_admin", "is_creator", "until_date",
        "can_manage_chat", "can_post_messages", "can_edit_messages",
        "can_delete_messages", "can_ban_users", "can_invite_users",
        "can_pin_messages", "can_promote_members", "can_change_info",
    )

    def __init__(self, lib, ptr: int) -> None:
        user_ptr = lib.tg_member_user(ptr)
        self.user = User(lib, user_ptr) if user_ptr else None

        raw = lib.tg_member_status(ptr)
        self.status: str = raw.decode() if raw else "member"
        self.is_admin:   bool = bool(lib.tg_member_is_admin(ptr))
        self.is_creator: bool = bool(lib.tg_member_is_creator(ptr))
        self.until_date: int  = lib.tg_member_until_date(ptr)
        self.can_ban_users:       bool = bool(lib.tg_member_can_ban(ptr))
        self.can_delete_messages: bool = bool(lib.tg_member_can_delete_msgs(ptr))
        self.can_invite_users:    bool = bool(lib.tg_member_can_invite(ptr))
        self.can_pin_messages:    bool = bool(lib.tg_member_can_pin(ptr))
        # These require direct struct access; default False until struct ctypes added
        self.can_manage_chat      = False
        self.can_post_messages    = False
        self.can_edit_messages    = False
        self.can_promote_members  = False
        self.can_change_info      = False

    def __repr__(self) -> str:
        return f"<ChatMember user={self.user!r} status={self.status!r}>"


# ── File ───────────────────────────────────────────────────────────────────── #

class File:
    """Wrapper around tg_file_t*.

    Attributes:
        id:            TDLib file ID.
        size:          File size in bytes.
        local_path:    Local path if downloaded, else empty string.
        is_downloaded: True if the file is fully downloaded.
        mime_type:     MIME type (may be empty).
        file_name:     Original file name (may be empty).
    """

    __slots__ = ("id", "size", "local_path", "is_downloaded",
                 "mime_type", "file_name")

    def __init__(self, lib, ptr: int) -> None:
        self.id:            int  = lib.tg_file_id(ptr)
        self.size:          int  = lib.tg_file_size(ptr)
        self.is_downloaded: bool = bool(lib.tg_file_is_downloaded(ptr))
        raw = lib.tg_file_local_path(ptr)
        self.local_path: str = raw.decode() if raw else ""
        raw = lib.tg_file_mime_type(ptr)
        self.mime_type: str = raw.decode() if raw else ""
        raw = lib.tg_file_name(ptr)
        self.file_name: str = raw.decode() if raw else ""

    def __repr__(self) -> str:
        return f"<File id={self.id} size={self.size} name={self.file_name!r}>"


# ── Message ────────────────────────────────────────────────────────────────── #

class Message:
    """Wrapper around tg_message_t* — eagerly copies all fields.

    Safe to store outside the handler callback.

    Attributes:
        id:               Message ID.
        chat_id:          Chat ID.
        sender_id:        Sender user/chat ID.
        text:             Message text, or None.
        caption:          Media caption, or None.
        is_out:           True if sent by current user.
        reply_to_id:      ID of replied-to message, or 0.
        is_private:       True if private chat.
        is_group:         True if group/supergroup.
        is_channel:       True if channel.
        date:             Unix timestamp.
        views:            View count.
        sender_chat_id:   Sender chat ID (for channel posts), or 0.
        media_type:       MediaType enum.
        file_id:          Primary media file ID, or 0.
        from_user:        User object if sender is a user, else None.
        reply_to_message: Replied-to Message object, or None.
        has_photo:        True if message contains a photo.
        has_video:        True if message contains a video.
        has_audio:        True if message contains audio.
        has_document:     True if message contains a document.
        has_sticker:      True if message contains a sticker.
        has_voice:        True if message contains a voice note.
        has_animation:    True if message contains an animation/GIF.
        has_location:     True if message contains a location.
        has_contact:      True if message contains a contact.

    Example::

        @client.on_message(TG_FILTER_INCOMING | TG_FILTER_TEXT)
        async def handler(client, msg):
            print(msg.text, msg.chat_id)
    """

    __slots__ = (
        "_lib", "_ptr",
        "id", "chat_id", "sender_id", "text", "caption",
        "is_out", "reply_to_id",
        "is_private", "is_group", "is_channel",
        "date", "views", "sender_chat_id",
        "media_type", "file_id",
        "has_photo", "has_video", "has_audio", "has_document",
        "has_sticker", "has_voice", "has_animation",
        "has_location", "has_contact",
        "from_user", "reply_to_message",
    )

    def __init__(self, lib, ptr: int) -> None:
        # RU: Сразу считываем все поля пока указатель валиден.
        self._lib = lib
        self._ptr = ptr

        self.id              = lib.tg_msg_id(ptr)
        self.chat_id         = lib.tg_msg_chat_id(ptr)
        self.sender_id       = lib.tg_msg_sender_id(ptr)
        self.is_out          = bool(lib.tg_msg_is_out(ptr))
        self.reply_to_id     = lib.tg_msg_reply_to(ptr)
        self.is_private      = bool(lib.tg_msg_is_private(ptr))
        self.is_group        = bool(lib.tg_msg_is_group(ptr))
        self.is_channel      = bool(lib.tg_msg_is_channel(ptr))
        self.date            = lib.tg_msg_date(ptr)
        self.views           = lib.tg_msg_views(ptr)
        self.sender_chat_id  = lib.tg_msg_sender_chat_id(ptr)
        self.file_id         = lib.tg_msg_file_id(ptr)
        self.has_photo       = bool(lib.tg_msg_has_photo(ptr))
        self.has_video       = bool(lib.tg_msg_has_video(ptr))
        self.has_audio       = bool(lib.tg_msg_has_audio(ptr))
        self.has_document    = bool(lib.tg_msg_has_document(ptr))
        self.has_sticker     = bool(lib.tg_msg_has_sticker(ptr))
        self.has_voice       = bool(lib.tg_msg_has_voice(ptr))
        self.has_animation   = bool(lib.tg_msg_has_animation(ptr))
        self.has_location    = bool(lib.tg_msg_has_location(ptr))
        self.has_contact     = bool(lib.tg_msg_has_contact(ptr))
        self.media_type      = MediaType(lib.tg_msg_media_type(ptr))

        raw = lib.tg_msg_text(ptr)
        self.text: Optional[str] = raw.decode("utf-8", errors="replace") if raw else None
        raw = lib.tg_msg_caption(ptr)
        self.caption: Optional[str] = raw.decode("utf-8", errors="replace") if raw else None

        # from_user — pointer to embedded tg_user_t, may be NULL
        user_ptr = lib.tg_msg_from_user(ptr)
        self.from_user: Optional[User] = User(lib, user_ptr) if user_ptr else None

        # reply_to_message — heap-allocated, usually NULL
        reply_ptr = lib.tg_msg_reply_to_message(ptr)
        self.reply_to_message: Optional["Message"] = (
            Message(lib, reply_ptr) if reply_ptr else None
        )

    def __repr__(self) -> str:
        return (f"<Message id={self.id} chat_id={self.chat_id} "
                f"text={self.text!r:.40}>")


__all__ = ["MediaType", "User", "Chat", "ChatMember", "File", "Message"]

