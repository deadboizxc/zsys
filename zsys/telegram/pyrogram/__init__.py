"""
zsys.telegram.pyrogram — Pyrogram userbot/bot.

Основной класс: PyrogramClient(pyrogram.Client, IClient)
"""

from .client import PyrogramClient, PyrogramConfig
from .decorators import with_reply, with_args
from .session import SessionConfig, create_session, validate_session, get_session_path
from .interact import interact_with, interact_with_to_delete, wait_for_reply
from .multi_client import MultiClient, command, MODULE_COMMANDS, ConsoleClient
from .message import (
    bold,
    italic,
    code,
    preformatted,
    link,
    mention,
    human_time,
    current_timestamp,
    split_text,
    rate_limit,
    escape_html,
)
from .context import PyrogramContext
from .router import attach_router
from .watcher import ModuleWatcher, start_watcher, stop_watcher, get_watcher

__all__ = [
    "PyrogramClient",
    "PyrogramConfig",
    "with_reply",
    "with_args",
    "SessionConfig",
    "create_session",
    "validate_session",
    "get_session_path",
    "interact_with",
    "interact_with_to_delete",
    "wait_for_reply",
    "MultiClient",
    "command",
    "MODULE_COMMANDS",
    "ConsoleClient",
    "bold",
    "italic",
    "code",
    "preformatted",
    "link",
    "mention",
    "human_time",
    "current_timestamp",
    "split_text",
    "rate_limit",
    "escape_html",
    "PyrogramContext",
    "attach_router",
    "ModuleWatcher",
    "start_watcher",
    "stop_watcher",
    "get_watcher",
]
