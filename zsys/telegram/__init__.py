"""zsys.telegram — Telegram client built on TDLib via libtg (C wrapper).

Single implementation: zsys.telegram.tdlib
  TdlibClient  — userbot / bot client (replaces Pyrogram/Telethon/aiogram)
  TdlibConfig  — configuration
  filters      — composable message filters (&, |, ~)
  errors       — FloodWait, RPCError, MessageDeleteForbidden, ...
  types        — Message, User, Chat, ChatMember, File

Quick start::

    from zsys.telegram import TdlibClient, TdlibConfig, filters

    cfg = TdlibConfig(api_id=123456, api_hash="abc123")
    client = TdlibClient(cfg)
    await client.start()
    await client.idle()
"""

from zsys.telegram.tdlib import TdlibClient, TdlibConfig, errors, filters
from zsys.telegram.tdlib.types import Chat, ChatMember, File, Message, User

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
