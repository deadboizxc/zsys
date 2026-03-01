# -*- coding: utf-8 -*-
"""Text formatting utilities for zsys core.

Provides HTML formatting functions for Telegram messages.
"""

from typing import Optional

__all__ = [
    "bold",
    "italic",
    "underline",
    "strikethrough",
    "code",
    "pre",
    "preformatted",
    "spoiler",
    "link",
    "mention",
    "quote",
    "escape_html",
]

try:
    from zsys._core import (
        escape_html,
        format_bold as bold,
        format_italic as italic,
        format_underline as underline,
        format_strikethrough as strikethrough,
        format_code as code,
        format_pre as pre,
        format_preformatted as preformatted,
        format_spoiler as spoiler,
        format_link as link,
        format_mention as mention,
        format_quote as quote,
        C_AVAILABLE,
    )
except ImportError:
    C_AVAILABLE = False

    def escape_html(text: str) -> str:
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def bold(text: str) -> str:
        return f"<b>{text}</b>"

    def italic(text: str) -> str:
        return f"<i>{text}</i>"

    def underline(text: str) -> str:
        return f"<u>{text}</u>"

    def strikethrough(text: str) -> str:
        return f"<s>{text}</s>"

    def code(text: str) -> str:
        return f"<code>{text}</code>"

    def pre(text: str, language: Optional[str] = None) -> str:
        if language:
            return f'<pre language="{language}">{text}</pre>'
        return f"<pre>{text}</pre>"

    def preformatted(text: str) -> str:
        return f"<pre>{text}</pre>"

    def spoiler(text: str) -> str:
        return f"<tg-spoiler>{text}</tg-spoiler>"

    def link(text: str, url: str) -> str:
        return f'<a href="{url}">{text}</a>'

    def mention(text: str, user_id: int) -> str:
        return f'<a href="tg://user?id={user_id}">{text}</a>'

    def quote(text: str) -> str:
        return f"<blockquote>{text}</blockquote>"
