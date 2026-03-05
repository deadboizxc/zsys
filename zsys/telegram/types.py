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

from enum import IntEnum
from typing import Optional

# ── Media type enum ────────────────────────────────────────────────────────── #


class MediaType(IntEnum):
    """Maps to tg_media_type_t in tg.h."""

    NONE = 0
    PHOTO = 1
    VIDEO = 2
    AUDIO = 3
    DOCUMENT = 4
    STICKER = 5
    VOICE = 6
    ANIMATION = 7
    VIDEO_NOTE = 8
    LOCATION = 9
    CONTACT = 10
    POLL = 11
    DICE = 12
    VENUE = 13


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

    __slots__ = (
        "id",
        "first_name",
        "last_name",
        "username",
        "phone",
        "is_bot",
        "is_premium",
    )

    def __init__(self, lib, ptr: int) -> None:
        # RU: Копируем поля пока указатель валиден.
        self.id: int = lib.tg_user_id(ptr)
        self.is_bot: bool = bool(lib.tg_user_is_bot(ptr))
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
        return (
            f"<User id={self.id} username={self.username!r} name={self.first_name!r}>"
        )


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

    __slots__ = (
        "id",
        "title",
        "username",
        "type",
        "members_count",
        "linked_chat_id",
        "permissions",
        "is_verified",
    )

    def __init__(self, lib, ptr: int) -> None:
        self.id: int = lib.tg_chat_id(ptr)
        self.members_count: int = lib.tg_chat_members_count(ptr)
        self.linked_chat_id: int = lib.tg_chat_linked_chat_id(ptr)
        self.permissions: int = lib.tg_chat_permissions(ptr)
        self.is_verified: bool = False

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
        "user",
        "status",
        "is_admin",
        "is_creator",
        "until_date",
        "can_manage_chat",
        "can_post_messages",
        "can_edit_messages",
        "can_delete_messages",
        "can_ban_users",
        "can_invite_users",
        "can_pin_messages",
        "can_promote_members",
        "can_change_info",
    )

    def __init__(self, lib, ptr: int) -> None:
        user_ptr = lib.tg_member_user(ptr)
        self.user = User(lib, user_ptr) if user_ptr else None

        raw = lib.tg_member_status(ptr)
        self.status: str = raw.decode() if raw else "member"
        self.is_admin: bool = bool(lib.tg_member_is_admin(ptr))
        self.is_creator: bool = bool(lib.tg_member_is_creator(ptr))
        self.until_date: int = lib.tg_member_until_date(ptr)
        self.can_ban_users: bool = bool(lib.tg_member_can_ban(ptr))
        self.can_delete_messages: bool = bool(lib.tg_member_can_delete_msgs(ptr))
        self.can_invite_users: bool = bool(lib.tg_member_can_invite(ptr))
        self.can_pin_messages: bool = bool(lib.tg_member_can_pin(ptr))
        # These require direct struct access; default False until struct ctypes added
        self.can_manage_chat = False
        self.can_post_messages = False
        self.can_edit_messages = False
        self.can_promote_members = False
        self.can_change_info = False

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

    __slots__ = ("id", "size", "local_path", "is_downloaded", "mime_type", "file_name")

    def __init__(self, lib, ptr: int) -> None:
        self.id: int = lib.tg_file_id(ptr)
        self.size: int = lib.tg_file_size(ptr)
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
        "_lib",
        "_ptr",
        "id",
        "chat_id",
        "sender_id",
        "text",
        "caption",
        "is_out",
        "reply_to_id",
        "is_private",
        "is_group",
        "is_channel",
        "date",
        "views",
        "sender_chat_id",
        "media_type",
        "file_id",
        "has_photo",
        "has_video",
        "has_audio",
        "has_document",
        "has_sticker",
        "has_voice",
        "has_animation",
        "has_location",
        "has_contact",
        "from_user",
        "reply_to_message",
    )

    def __init__(self, lib, ptr: int) -> None:
        # RU: Сразу считываем все поля пока указатель валиден.
        self._lib = lib
        self._ptr = ptr

        self.id = lib.tg_msg_id(ptr)
        self.chat_id = lib.tg_msg_chat_id(ptr)
        self.sender_id = lib.tg_msg_sender_id(ptr)
        self.is_out = bool(lib.tg_msg_is_out(ptr))
        self.reply_to_id = lib.tg_msg_reply_to(ptr)
        self.is_private = bool(lib.tg_msg_is_private(ptr))
        self.is_group = bool(lib.tg_msg_is_group(ptr))
        self.is_channel = bool(lib.tg_msg_is_channel(ptr))
        self.date = lib.tg_msg_date(ptr)
        self.views = lib.tg_msg_views(ptr)
        self.sender_chat_id = lib.tg_msg_sender_chat_id(ptr)
        self.file_id = lib.tg_msg_file_id(ptr)
        self.has_photo = bool(lib.tg_msg_has_photo(ptr))
        self.has_video = bool(lib.tg_msg_has_video(ptr))
        self.has_audio = bool(lib.tg_msg_has_audio(ptr))
        self.has_document = bool(lib.tg_msg_has_document(ptr))
        self.has_sticker = bool(lib.tg_msg_has_sticker(ptr))
        self.has_voice = bool(lib.tg_msg_has_voice(ptr))
        self.has_animation = bool(lib.tg_msg_has_animation(ptr))
        self.has_location = bool(lib.tg_msg_has_location(ptr))
        self.has_contact = bool(lib.tg_msg_has_contact(ptr))
        self.media_type = MediaType(lib.tg_msg_media_type(ptr))

        raw = lib.tg_msg_text(ptr)
        self.text: Optional[str] = (
            raw.decode("utf-8", errors="replace") if raw else None
        )
        raw = lib.tg_msg_caption(ptr)
        self.caption: Optional[str] = (
            raw.decode("utf-8", errors="replace") if raw else None
        )

        # from_user — pointer to embedded tg_user_t, may be NULL
        user_ptr = lib.tg_msg_from_user(ptr)
        self.from_user: Optional[User] = User(lib, user_ptr) if user_ptr else None

        # reply_to_message — heap-allocated, usually NULL
        reply_ptr = lib.tg_msg_reply_to_message(ptr)
        self.reply_to_message: Optional["Message"] = (
            Message(lib, reply_ptr) if reply_ptr else None
        )

    def __repr__(self) -> str:
        return f"<Message id={self.id} chat_id={self.chat_id} text={self.text!r:.40}>"


# ── Additional Types (Pyrogram compatibility) ─────────────────────────────── #


class ChatPermissions:
    """Chat member permissions."""

    def __init__(
        self,
        can_send_messages: bool = False,
        can_send_media_messages: bool = False,
        can_send_other_messages: bool = False,
        can_add_web_page_previews: bool = False,
        can_send_polls: bool = False,
        can_change_info: bool = False,
        can_invite_users: bool = False,
        can_pin_messages: bool = False,
    ):
        self.can_send_messages = can_send_messages
        self.can_send_media_messages = can_send_media_messages
        self.can_send_other_messages = can_send_other_messages
        self.can_add_web_page_previews = can_add_web_page_previews
        self.can_send_polls = can_send_polls
        self.can_change_info = can_change_info
        self.can_invite_users = can_invite_users
        self.can_pin_messages = can_pin_messages


class ChatPrivileges:
    """Admin privileges."""

    def __init__(
        self,
        can_manage_chat: bool = False,
        can_delete_messages: bool = False,
        can_manage_video_chats: bool = False,
        can_restrict_members: bool = False,
        can_promote_members: bool = False,
        can_change_info: bool = False,
        can_invite_users: bool = False,
        can_pin_messages: bool = False,
        is_anonymous: bool = False,
    ):
        self.can_manage_chat = can_manage_chat
        self.can_delete_messages = can_delete_messages
        self.can_manage_video_chats = can_manage_video_chats
        self.can_restrict_members = can_restrict_members
        self.can_promote_members = can_promote_members
        self.can_change_info = can_change_info
        self.can_invite_users = can_invite_users
        self.can_pin_messages = can_pin_messages
        self.is_anonymous = is_anonymous


class InlineKeyboardButton:
    """Inline keyboard button."""

    def __init__(
        self,
        text: str,
        callback_data: Optional[str] = None,
        url: Optional[str] = None,
        switch_inline_query: Optional[str] = None,
    ):
        self.text = text
        self.callback_data = callback_data
        self.url = url
        self.switch_inline_query = switch_inline_query

    def to_dict(self) -> dict:
        d = {"text": self.text}
        if self.url:
            d["url"] = self.url
        elif self.callback_data:
            d["callback_data"] = self.callback_data
        elif self.switch_inline_query:
            d["switch_inline_query"] = self.switch_inline_query
        return d


class InlineKeyboardMarkup:
    """Inline keyboard markup."""

    def __init__(self, inline_keyboard: list[list[InlineKeyboardButton]]):
        self.inline_keyboard = inline_keyboard

    def to_dict(self) -> dict:
        return {
            "inline_keyboard": [
                [btn.to_dict() for btn in row]
                for row in self.inline_keyboard
            ]
        }


class InputMediaPhoto:
    """Input media photo for media groups."""

    def __init__(self, media: str, caption: str = "", parse_mode: str = ""):
        self.type = "photo"
        self.media = media
        self.caption = caption
        self.parse_mode = parse_mode


class InputMediaVideo:
    """Input media video for media groups."""

    def __init__(self, media: str, caption: str = "", parse_mode: str = ""):
        self.type = "video"
        self.media = media
        self.caption = caption
        self.parse_mode = parse_mode


class InputMediaAudio:
    """Input media audio for media groups."""

    def __init__(self, media: str, caption: str = "", parse_mode: str = ""):
        self.type = "audio"
        self.media = media
        self.caption = caption
        self.parse_mode = parse_mode


class InputMediaDocument:
    """Input media document for media groups."""

    def __init__(self, media: str, caption: str = "", parse_mode: str = ""):
        self.type = "document"
        self.media = media
        self.caption = caption
        self.parse_mode = parse_mode


# ── Reply Keyboard Types ───────────────────────────────────────────────────── #


class ReplyKeyboardButton:
    """Reply keyboard button."""

    def __init__(
        self,
        text: str,
        request_contact: bool = False,
        request_location: bool = False,
        request_poll: Optional[str] = None,  # "quiz" or "regular"
    ):
        self.text = text
        self.request_contact = request_contact
        self.request_location = request_location
        self.request_poll = request_poll

    def to_dict(self) -> dict:
        d = {"text": self.text}
        if self.request_contact:
            d["request_contact"] = True
        if self.request_location:
            d["request_location"] = True
        if self.request_poll:
            d["request_poll"] = {"type": self.request_poll}
        return d


class ReplyKeyboardMarkup:
    """Reply keyboard markup."""

    def __init__(
        self,
        keyboard: list[list[ReplyKeyboardButton]],
        resize_keyboard: bool = True,
        one_time_keyboard: bool = False,
        is_persistent: bool = False,
        input_field_placeholder: Optional[str] = None,
    ):
        self.keyboard = keyboard
        self.resize_keyboard = resize_keyboard
        self.one_time_keyboard = one_time_keyboard
        self.is_persistent = is_persistent
        self.input_field_placeholder = input_field_placeholder

    def to_dict(self) -> dict:
        d = {
            "keyboard": [[btn.to_dict() for btn in row] for row in self.keyboard],
            "resize_keyboard": self.resize_keyboard,
            "one_time_keyboard": self.one_time_keyboard,
            "is_persistent": self.is_persistent,
        }
        if self.input_field_placeholder:
            d["input_field_placeholder"] = self.input_field_placeholder
        return d


class ReplyKeyboardRemove:
    """Remove reply keyboard."""

    def __init__(self, selective: bool = False):
        self.selective = selective

    def to_dict(self) -> dict:
        return {"remove_keyboard": True, "selective": self.selective}


class ForceReply:
    """Force reply markup."""

    def __init__(
        self,
        selective: bool = False,
        input_field_placeholder: Optional[str] = None,
    ):
        self.selective = selective
        self.input_field_placeholder = input_field_placeholder

    def to_dict(self) -> dict:
        d = {"force_reply": True, "selective": self.selective}
        if self.input_field_placeholder:
            d["input_field_placeholder"] = self.input_field_placeholder
        return d


# ── Callback Query ─────────────────────────────────────────────────────────── #


class CallbackQuery:
    """Callback query from inline button press."""

    def __init__(
        self,
        id: str,
        from_user: Optional[User],
        chat_instance: str = "",
        message: Optional["Message"] = None,
        inline_message_id: Optional[str] = None,
        data: Optional[str] = None,
        game_short_name: Optional[str] = None,
    ):
        self.id = id
        self.from_user = from_user
        self.chat_instance = chat_instance
        self.message = message
        self.inline_message_id = inline_message_id
        self.data = data
        self.game_short_name = game_short_name

    async def answer(
        self,
        text: Optional[str] = None,
        show_alert: bool = False,
        url: Optional[str] = None,
        cache_time: int = 0,
    ) -> None:
        """Answer the callback query. Requires client reference."""
        pass  # Will be implemented via client method


# ── Inline Query ───────────────────────────────────────────────────────────── #


class InlineQuery:
    """Inline query from user."""

    def __init__(
        self,
        id: str,
        from_user: Optional[User],
        query: str,
        offset: str = "",
        chat_type: Optional[str] = None,
    ):
        self.id = id
        self.from_user = from_user
        self.query = query
        self.offset = offset
        self.chat_type = chat_type


# ── Inline Query Results ───────────────────────────────────────────────────── #


class InlineQueryResultArticle:
    """Inline query result - article."""

    def __init__(
        self,
        id: str,
        title: str,
        input_message_content: dict,
        url: Optional[str] = None,
        description: Optional[str] = None,
        thumb_url: Optional[str] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
    ):
        self.type = "article"
        self.id = id
        self.title = title
        self.input_message_content = input_message_content
        self.url = url
        self.description = description
        self.thumb_url = thumb_url
        self.reply_markup = reply_markup

    def to_dict(self) -> dict:
        d = {
            "type": self.type,
            "id": self.id,
            "title": self.title,
            "input_message_content": self.input_message_content,
        }
        if self.url:
            d["url"] = self.url
        if self.description:
            d["description"] = self.description
        if self.thumb_url:
            d["thumb_url"] = self.thumb_url
        if self.reply_markup:
            d["reply_markup"] = self.reply_markup.to_dict()
        return d


class InlineQueryResultPhoto:
    """Inline query result - photo."""

    def __init__(
        self,
        id: str,
        photo_url: str,
        thumb_url: str,
        photo_width: int = 0,
        photo_height: int = 0,
        title: Optional[str] = None,
        description: Optional[str] = None,
        caption: Optional[str] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
    ):
        self.type = "photo"
        self.id = id
        self.photo_url = photo_url
        self.thumb_url = thumb_url
        self.photo_width = photo_width
        self.photo_height = photo_height
        self.title = title
        self.description = description
        self.caption = caption
        self.reply_markup = reply_markup

    def to_dict(self) -> dict:
        d = {
            "type": self.type,
            "id": self.id,
            "photo_url": self.photo_url,
            "thumb_url": self.thumb_url,
        }
        if self.photo_width:
            d["photo_width"] = self.photo_width
        if self.photo_height:
            d["photo_height"] = self.photo_height
        if self.title:
            d["title"] = self.title
        if self.description:
            d["description"] = self.description
        if self.caption:
            d["caption"] = self.caption
        if self.reply_markup:
            d["reply_markup"] = self.reply_markup.to_dict()
        return d


# ── Message Entities ───────────────────────────────────────────────────────── #


class MessageEntity:
    """Message entity (bold, link, mention, etc.)."""

    def __init__(
        self,
        type: str,
        offset: int,
        length: int,
        url: Optional[str] = None,
        user: Optional[User] = None,
        language: Optional[str] = None,
        custom_emoji_id: Optional[str] = None,
    ):
        self.type = type  # "bold", "italic", "url", "mention", "code", etc.
        self.offset = offset
        self.length = length
        self.url = url
        self.user = user
        self.language = language
        self.custom_emoji_id = custom_emoji_id


# ── Photo / Video / Audio / Document ───────────────────────────────────────── #


class PhotoSize:
    """Photo size."""

    def __init__(
        self,
        file_id: str,
        file_unique_id: str,
        width: int,
        height: int,
        file_size: int = 0,
    ):
        self.file_id = file_id
        self.file_unique_id = file_unique_id
        self.width = width
        self.height = height
        self.file_size = file_size


class Video:
    """Video file."""

    def __init__(
        self,
        file_id: str,
        file_unique_id: str,
        width: int,
        height: int,
        duration: int,
        thumb: Optional[PhotoSize] = None,
        file_name: Optional[str] = None,
        mime_type: Optional[str] = None,
        file_size: int = 0,
    ):
        self.file_id = file_id
        self.file_unique_id = file_unique_id
        self.width = width
        self.height = height
        self.duration = duration
        self.thumb = thumb
        self.file_name = file_name
        self.mime_type = mime_type
        self.file_size = file_size


class Audio:
    """Audio file."""

    def __init__(
        self,
        file_id: str,
        file_unique_id: str,
        duration: int,
        performer: Optional[str] = None,
        title: Optional[str] = None,
        file_name: Optional[str] = None,
        mime_type: Optional[str] = None,
        file_size: int = 0,
        thumb: Optional[PhotoSize] = None,
    ):
        self.file_id = file_id
        self.file_unique_id = file_unique_id
        self.duration = duration
        self.performer = performer
        self.title = title
        self.file_name = file_name
        self.mime_type = mime_type
        self.file_size = file_size
        self.thumb = thumb


class Document:
    """Document file."""

    def __init__(
        self,
        file_id: str,
        file_unique_id: str,
        file_name: Optional[str] = None,
        mime_type: Optional[str] = None,
        file_size: int = 0,
        thumb: Optional[PhotoSize] = None,
    ):
        self.file_id = file_id
        self.file_unique_id = file_unique_id
        self.file_name = file_name
        self.mime_type = mime_type
        self.file_size = file_size
        self.thumb = thumb


class Sticker:
    """Sticker."""

    def __init__(
        self,
        file_id: str,
        file_unique_id: str,
        type: str,  # "regular", "mask", "custom_emoji"
        width: int,
        height: int,
        is_animated: bool = False,
        is_video: bool = False,
        emoji: Optional[str] = None,
        set_name: Optional[str] = None,
        thumb: Optional[PhotoSize] = None,
        file_size: int = 0,
    ):
        self.file_id = file_id
        self.file_unique_id = file_unique_id
        self.type = type
        self.width = width
        self.height = height
        self.is_animated = is_animated
        self.is_video = is_video
        self.emoji = emoji
        self.set_name = set_name
        self.thumb = thumb
        self.file_size = file_size


class Voice:
    """Voice message."""

    def __init__(
        self,
        file_id: str,
        file_unique_id: str,
        duration: int,
        mime_type: Optional[str] = None,
        file_size: int = 0,
    ):
        self.file_id = file_id
        self.file_unique_id = file_unique_id
        self.duration = duration
        self.mime_type = mime_type
        self.file_size = file_size


class VideoNote:
    """Video note (round video)."""

    def __init__(
        self,
        file_id: str,
        file_unique_id: str,
        length: int,
        duration: int,
        thumb: Optional[PhotoSize] = None,
        file_size: int = 0,
    ):
        self.file_id = file_id
        self.file_unique_id = file_unique_id
        self.length = length
        self.duration = duration
        self.thumb = thumb
        self.file_size = file_size


class Location:
    """Location."""

    def __init__(
        self,
        latitude: float,
        longitude: float,
        horizontal_accuracy: Optional[float] = None,
        live_period: Optional[int] = None,
        heading: Optional[int] = None,
        proximity_alert_radius: Optional[int] = None,
    ):
        self.latitude = latitude
        self.longitude = longitude
        self.horizontal_accuracy = horizontal_accuracy
        self.live_period = live_period
        self.heading = heading
        self.proximity_alert_radius = proximity_alert_radius


class Contact:
    """Contact."""

    def __init__(
        self,
        phone_number: str,
        first_name: str,
        last_name: Optional[str] = None,
        user_id: Optional[int] = None,
        vcard: Optional[str] = None,
    ):
        self.phone_number = phone_number
        self.first_name = first_name
        self.last_name = last_name
        self.user_id = user_id
        self.vcard = vcard


class Poll:
    """Poll."""

    def __init__(
        self,
        id: str,
        question: str,
        options: list,
        total_voter_count: int,
        is_closed: bool = False,
        is_anonymous: bool = True,
        type: str = "regular",  # "regular" or "quiz"
        allows_multiple_answers: bool = False,
        correct_option_id: Optional[int] = None,
        explanation: Optional[str] = None,
    ):
        self.id = id
        self.question = question
        self.options = options
        self.total_voter_count = total_voter_count
        self.is_closed = is_closed
        self.is_anonymous = is_anonymous
        self.type = type
        self.allows_multiple_answers = allows_multiple_answers
        self.correct_option_id = correct_option_id
        self.explanation = explanation


class Dice:
    """Dice animation."""

    def __init__(self, emoji: str, value: int):
        self.emoji = emoji
        self.value = value


# ── Reaction ───────────────────────────────────────────────────────────────── #


class ReactionTypeEmoji:
    """Reaction with emoji."""

    def __init__(self, emoji: str):
        self.type = "emoji"
        self.emoji = emoji

    def to_dict(self) -> dict:
        return {"type": self.type, "emoji": self.emoji}


class ReactionTypeCustomEmoji:
    """Reaction with custom emoji."""

    def __init__(self, custom_emoji_id: str):
        self.type = "custom_emoji"
        self.custom_emoji_id = custom_emoji_id

    def to_dict(self) -> dict:
        return {"type": self.type, "custom_emoji_id": self.custom_emoji_id}


__all__ = [
    "MediaType",
    "User",
    "Chat",
    "ChatMember",
    "File",
    "Message",
    "ChatPermissions",
    "ChatPrivileges",
    "InlineKeyboardButton",
    "InlineKeyboardMarkup",
    "ReplyKeyboardButton",
    "ReplyKeyboardMarkup",
    "ReplyKeyboardRemove",
    "ForceReply",
    "CallbackQuery",
    "InlineQuery",
    "InlineQueryResultArticle",
    "InlineQueryResultPhoto",
    "MessageEntity",
    "PhotoSize",
    "Video",
    "Audio",
    "Document",
    "Sticker",
    "Voice",
    "VideoNote",
    "Location",
    "Contact",
    "Poll",
    "Dice",
    "ReactionTypeEmoji",
    "ReactionTypeCustomEmoji",
    "InputMediaPhoto",
    "InputMediaVideo",
    "InputMediaAudio",
    "InputMediaDocument",
]
