"""zsys.telegram — Telegram client built on TDLib via libtg (C wrapper).

Single implementation using TDLib C library.
  TdlibClient  — userbot / bot client (replaces Pyrogram/Telethon/aiogram)
  TdlibConfig  — configuration
  filters      — composable message filters (&, |, ~)
  errors       — FloodWait, RPCError, MessageDeleteForbidden, ...
  types        — Message, User, Chat, ChatMember, File

For Pyrogram compatibility:
  from zsys.telegram.pyrogram import PyrogramClient, PyrogramConfig

Quick start::

    from zsys.telegram import TdlibClient, TdlibConfig, filters

    cfg = TdlibConfig(api_id=123456, api_hash="abc123")
    client = TdlibClient(cfg)
    await client.start()
    await client.idle()
"""

from zsys.telegram import errors, filters
from zsys.telegram.client import TdlibClient
from zsys.telegram.config import TdlibConfig
from zsys.telegram.types import Chat, ChatMember, File, Message, User

__all__ = [
    "TdlibClient",
    "TdlibConfig",
    "filters",
    "errors",
    "Message",
    "User",
    "Chat",
    "ChatMember",
    "File",
]
