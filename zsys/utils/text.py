# -*- coding: utf-8 -*-
"""Text formatting utilities — HTML tag helpers for Telegram messages.

Provides thin wrapper functions that produce Telegram-compatible HTML markup:
bold, italic, underline, code blocks, spoilers, links, and mention tags.
C extension is used when available; pure-Python fallback is always present.
"""
# RU: Утилиты форматирования текста — вспомогательные HTML-функции для Telegram.
# RU: C-расширение используется при наличии; иначе активен чистый Python-fallback.

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
        """Escape special HTML characters in text.

        Converts &, <, > to their HTML entity equivalents
        to prevent HTML injection in Telegram messages.

        Args:
            text: Raw text to escape.

        Returns:
            str: HTML-escaped text.
        """
        # RU: Экранирует специальные HTML-символы в тексте.
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def bold(text: str) -> str:
        """Wrap text in HTML bold tags.

        Args:
            text: Text to format.

        Returns:
            str: Bold-formatted HTML string.
        """
        # RU: Оборачивает текст в HTML-теги жирного шрифта.
        return f"<b>{text}</b>"

    def italic(text: str) -> str:
        """Wrap text in HTML italic tags.

        Args:
            text: Text to format.

        Returns:
            str: Italic-formatted HTML string.
        """
        # RU: Оборачивает текст в HTML-теги курсивного шрифта.
        return f"<i>{text}</i>"

    def underline(text: str) -> str:
        """Wrap text in HTML underline tags.

        Args:
            text: Text to format.

        Returns:
            str: Underline-formatted HTML string.
        """
        # RU: Оборачивает текст в HTML-теги подчёркивания.
        return f"<u>{text}</u>"

    def strikethrough(text: str) -> str:
        """Wrap text in HTML strikethrough tags.

        Args:
            text: Text to format.

        Returns:
            str: Strikethrough-formatted HTML string.
        """
        # RU: Оборачивает текст в HTML-теги зачёркивания.
        return f"<s>{text}</s>"

    def code(text: str) -> str:
        """Wrap text in HTML inline code tags.

        Args:
            text: Text to format.

        Returns:
            str: Inline-code-formatted HTML string.
        """
        # RU: Оборачивает текст в HTML-теги встроенного кода.
        return f"<code>{text}</code>"

    def pre(text: str, language: Optional[str] = None) -> str:
        """Wrap text in HTML pre block, optionally with a language attribute.

        Used for code blocks in Telegram HTML mode.

        Args:
            text: Text to format.
            language: Optional programming language for syntax highlighting.

        Returns:
            str: Preformatted HTML block string.
        """
        # RU: Оборачивает текст в HTML-блок предварительного форматирования с опциональным языком.
        if language:
            return f'<pre language="{language}">{text}</pre>'
        return f"<pre>{text}</pre>"

    def preformatted(text: str) -> str:
        """Wrap text in plain HTML pre block without language attribute.

        Args:
            text: Text to format.

        Returns:
            str: Preformatted HTML block string.
        """
        # RU: Оборачивает текст в простой HTML-блок предварительного форматирования.
        return f"<pre>{text}</pre>"

    def spoiler(text: str) -> str:
        """Wrap text in Telegram spoiler tags.

        Args:
            text: Text to hide as spoiler.

        Returns:
            str: Spoiler-formatted HTML string.
        """
        # RU: Оборачивает текст в теги Telegram-спойлера.
        return f"<tg-spoiler>{text}</tg-spoiler>"

    def link(text: str, url: str) -> str:
        """Create an HTML hyperlink.

        Args:
            text: Display text for the link.
            url: Target URL.

        Returns:
            str: HTML anchor tag string.
        """
        # RU: Создаёт HTML-гиперссылку с указанным текстом и адресом.
        return f'<a href="{url}">{text}</a>'

    def mention(text: str, user_id: int) -> str:
        """Create a Telegram user mention link.

        Args:
            text: Display text for the mention.
            user_id: Telegram user ID to mention.

        Returns:
            str: HTML mention link string.
        """
        # RU: Создаёт ссылку-упоминание пользователя Telegram по его ID.
        return f'<a href="tg://user?id={user_id}">{text}</a>'

    def quote(text: str) -> str:
        """Wrap text in HTML blockquote tags.

        Args:
            text: Text to format as a quote.

        Returns:
            str: Blockquote-formatted HTML string.
        """
        # RU: Оборачивает текст в HTML-теги блочной цитаты.
        return f"<blockquote>{text}</blockquote>"
