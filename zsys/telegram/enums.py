"""zsys.telegram.enums — Telegram enumerations."""
from enum import Enum


class ParseMode(str, Enum):
    """Parse mode for messages."""
    DISABLED = ""
    MARKDOWN = "markdown"
    HTML = "html"


class ChatType(str, Enum):
    """Chat type."""
    PRIVATE = "private"
    BOT = "bot"
    GROUP = "group"
    SUPERGROUP = "supergroup"
    CHANNEL = "channel"


class ChatMemberStatus(str, Enum):
    """Chat member status."""
    OWNER = "creator"
    ADMINISTRATOR = "administrator"
    MEMBER = "member"
    RESTRICTED = "restricted"
    LEFT = "left"
    BANNED = "kicked"


class ChatAction(str, Enum):
    """Chat actions for send_chat_action."""
    TYPING = "typing"
    UPLOAD_PHOTO = "upload_photo"
    RECORD_VIDEO = "record_video"
    UPLOAD_VIDEO = "upload_video"
    RECORD_VOICE = "record_voice"
    UPLOAD_VOICE = "upload_voice"
    UPLOAD_DOCUMENT = "upload_document"
    FIND_LOCATION = "find_location"
    RECORD_VIDEO_NOTE = "record_video_note"
    UPLOAD_VIDEO_NOTE = "upload_video_note"
    CANCEL = "cancel"


class MessageEntityType(str, Enum):
    """Message entity types."""
    MENTION = "mention"
    HASHTAG = "hashtag"
    CASHTAG = "cashtag"
    BOT_COMMAND = "bot_command"
    URL = "url"
    EMAIL = "email"
    PHONE_NUMBER = "phone_number"
    BOLD = "bold"
    ITALIC = "italic"
    UNDERLINE = "underline"
    STRIKETHROUGH = "strikethrough"
    SPOILER = "spoiler"
    CODE = "code"
    PRE = "pre"
    TEXT_LINK = "text_link"
    TEXT_MENTION = "text_mention"
    CUSTOM_EMOJI = "custom_emoji"


class UserStatus(str, Enum):
    """User online status."""
    ONLINE = "online"
    OFFLINE = "offline"
    RECENTLY = "recently"
    LAST_WEEK = "last_week"
    LAST_MONTH = "last_month"
    LONG_AGO = "long_ago"


class MessageMediaType(str, Enum):
    """Media types in messages."""
    PHOTO = "photo"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    STICKER = "sticker"
    ANIMATION = "animation"
    VOICE = "voice"
    VIDEO_NOTE = "video_note"
    CONTACT = "contact"
    LOCATION = "location"
    VENUE = "venue"
    POLL = "poll"
    DICE = "dice"
    WEB_PAGE = "web_page"


__all__ = [
    "ParseMode",
    "ChatType",
    "ChatMemberStatus",
    "ChatAction",
    "MessageEntityType",
    "UserStatus",
    "MessageMediaType",
]
