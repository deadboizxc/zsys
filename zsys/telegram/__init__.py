"""zsys.telegram — Telegram client built on TDLib via libtg (C wrapper).

Single implementation using TDLib C library.
  TdlibClient  — userbot / bot client (replaces Pyrogram/Telethon/aiogram)
  TdlibConfig  — configuration
  filters      — composable message filters (&, |, ~)
  errors       — FloodWait, RPCError, MessageDeleteForbidden, ...
  types        — Message, User, Chat, ChatMember, File, keyboards, reactions

Quick start::

    from zsys.telegram import TdlibClient, TdlibConfig, filters

    cfg = TdlibConfig(api_id=123456, api_hash="abc123")
    client = TdlibClient(cfg)
    await client.start()
    await client.idle()

TDLib auto-install:
    TDLib downloads automatically on first import. To install manually:
    - python -m zsys.telegram.tdlib_installer
    - or: zsys/telegram/scripts/install_tdlib.sh
"""
import os as _os

__version__ = "1.0.0"
__tdlib_version__ = "1.8.0"

from zsys.telegram import errors, filters
from zsys.telegram.config import TdlibConfig
from zsys.telegram.types import (
    Audio,
    CallbackQuery,
    Chat,
    ChatMember,
    ChatPermissions,
    ChatPrivileges,
    Contact,
    Dice,
    Document,
    File,
    ForceReply,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQuery,
    InlineQueryResultArticle,
    InlineQueryResultPhoto,
    InputMediaAudio,
    InputMediaDocument,
    InputMediaPhoto,
    InputMediaVideo,
    Location,
    Message,
    MessageEntity,
    PhotoSize,
    Poll,
    ReactionTypeCustomEmoji,
    ReactionTypeEmoji,
    ReplyKeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Sticker,
    User,
    Video,
    VideoNote,
    Voice,
)

# Auto-check TDLib on import (skip if ZSYS_SKIP_TDLIB_CHECK=1)
if not _os.environ.get("ZSYS_SKIP_TDLIB_CHECK"):
    from zsys.telegram.tdlib_installer import find_libtg, find_tdjson
    _tdjson = find_tdjson()
    _libtg = find_libtg()
    if not _tdjson or not _libtg:
        import warnings
        _missing = []
        if not _tdjson:
            _missing.append("TDLib (libtdjson)")
        if not _libtg:
            _missing.append("libtg")
        warnings.warn(
            f"zsys.telegram: {', '.join(_missing)} not found. "
            f"Run: python -m zsys.telegram.tdlib_installer",
            RuntimeWarning,
            stacklevel=2
        )
    del find_libtg, find_tdjson, _tdjson, _libtg

from zsys.telegram.client import TdlibClient

__all__ = [
    # Core
    "TdlibClient",
    "TdlibConfig",
    "filters",
    "errors",
    # Types
    "Message",
    "User",
    "Chat",
    "ChatMember",
    "File",
    "ChatPermissions",
    "ChatPrivileges",
    # Keyboards
    "InlineKeyboardButton",
    "InlineKeyboardMarkup",
    "ReplyKeyboardButton",
    "ReplyKeyboardMarkup",
    "ReplyKeyboardRemove",
    "ForceReply",
    # Callback / Inline
    "CallbackQuery",
    "InlineQuery",
    "InlineQueryResultArticle",
    "InlineQueryResultPhoto",
    # Media types
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
    "MessageEntity",
    # Input media
    "InputMediaPhoto",
    "InputMediaVideo",
    "InputMediaAudio",
    "InputMediaDocument",
    # Reactions
    "ReactionTypeEmoji",
    "ReactionTypeCustomEmoji",
    # Meta
    "__version__",
    "__tdlib_version__",
]
