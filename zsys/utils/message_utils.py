"""Message formatting utilities for Telegram bots.

Provides helpers for formatting text with HTML/Markdown tags.
Supports bold, italic, code, links, mentions, truncation, and chunk-splitting.
"""
# RU: Утилиты форматирования сообщений для Telegram-ботов.
# RU: Содержит функции HTML-разметки, обрезки текста и разбиения на части для отправки.

import html
import re
from typing import Optional, List


def escape_html(text: str) -> str:
    """Escape HTML special characters.

    Args:
        text: Text to escape

    Returns:
        HTML-escaped text
    """
    # RU: Делегирует экранирование стандартной библиотеке html.
    return html.escape(text)


def format_bold(text: str, escape: bool = True) -> str:
    """Format text as bold.

    Args:
        text: Text to format
        escape: Whether to escape HTML (default True)

    Returns:
        Bold-formatted text
    """
    # RU: Оборачивает текст в HTML-тег <b> для жирного начертания.
    if escape:
        text = escape_html(text)
    return f"<b>{text}</b>"


def format_italic(text: str, escape: bool = True) -> str:
    """Format text as italic.

    Args:
        text: Text to format
        escape: Whether to escape HTML (default True)

    Returns:
        Italic-formatted text
    """
    # RU: Оборачивает текст в HTML-тег <i> для курсивного начертания.
    if escape:
        text = escape_html(text)
    return f"<i>{text}</i>"


def format_code(text: str, escape: bool = False) -> str:
    """Format text as inline code.

    Args:
        text: Text to format
        escape: Whether to escape HTML (default False, code is already escaped)

    Returns:
        Code-formatted text
    """
    # RU: Оборачивает текст в HTML-тег <code> для отображения в моноширинном шрифте.
    if escape:
        text = escape_html(text)
    return f"<code>{text}</code>"


def format_pre(text: str, language: Optional[str] = None, escape: bool = False) -> str:
    """Format text as code block.

    Args:
        text: Text to format
        language: Programming language for syntax highlighting
        escape: Whether to escape HTML (default False)

    Returns:
        Pre-formatted text
    """
    # RU: Оборачивает текст в <pre>, опционально вкладывая <code class='language-…'> для подсветки.
    if escape:
        text = escape_html(text)

    if language:
        return f"<pre><code class='language-{language}'>{text}</code></pre>"
    return f"<pre>{text}</pre>"


def format_link(text: str, url: str, escape: bool = True) -> str:
    """Format text as hyperlink.

    Args:
        text: Link text
        url: Link URL
        escape: Whether to escape text (default True)

    Returns:
        Link-formatted text
    """
    # RU: Создаёт HTML-гиперссылку с заданным URL и отображаемым текстом.
    if escape:
        text = escape_html(text)
    return f'<a href="{url}">{text}</a>'


def format_mention(text: str, user_id: int, escape: bool = True) -> str:
    """Format text as user mention.

    Args:
        text: Mention text
        user_id: User ID to mention
        escape: Whether to escape text (default True)

    Returns:
        Mention-formatted text
    """
    # RU: Создаёт упоминание пользователя через Telegram tg://user?id= ссылку.
    if escape:
        text = escape_html(text)
    return f'<a href="tg://user?id={user_id}">{text}</a>'


def format_mono(text: str, escape: bool = True) -> str:
    """Format text as monospace.

    Args:
        text: Text to format
        escape: Whether to escape HTML (default True)

    Returns:
        Monospace-formatted text
    """
    # RU: Псевдоним format_code — оборачивает текст в <code> для моноширинного вывода.
    if escape:
        text = escape_html(text)
    return f"<code>{text}</code>"


def truncate_text(text: str, max_length: int = 4096, suffix: str = "...") -> str:
    """Truncate text to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length (default 4096 - Telegram message limit)
        suffix: Suffix to add if truncated (default "...")

    Returns:
        Truncated text
    """
    # RU: Если текст укладывается в лимит — возвращает без изменений; иначе обрезает и добавляет суффикс.
    if len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix


def split_text(text: str, max_length: int = 4096) -> List[str]:
    """Split text into chunks for Telegram messages.

    Args:
        text: Text to split
        max_length: Maximum chunk length (default 4096)

    Returns:
        List of text chunks
    """
    # RU: Разбивает текст на части по переносам строк, не превышая max_length символов на часть.
    if len(text) <= max_length:
        return [text]

    chunks = []
    current_chunk = ""

    for line in text.split("\n"):
        if len(current_chunk) + len(line) + 1 <= max_length:
            current_chunk += line + "\n"
        else:
            if current_chunk:
                chunks.append(current_chunk)

            # If single line is too long, split it by max_length slices
            # RU: Одиночная строка длиннее лимита — нарезаем её на равные куски по max_length.
            if len(line) > max_length:
                for i in range(0, len(line), max_length):
                    chunks.append(line[i : i + max_length])
                current_chunk = ""
            else:
                current_chunk = line + "\n"

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def strip_markdown(text: str) -> str:
    """Remove Markdown formatting from text.

    Args:
        text: Text with Markdown

    Returns:
        Plain text
    """
    # RU: Последовательно применяет regex для удаления жирного, курсива, кода и ссылок Markdown.
    # Remove bold/italic
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)  # RU: **жирный** → жирный
    text = re.sub(r"__(.+?)__", r"\1", text)  # RU: __жирный__ → жирный
    text = re.sub(r"\*(.+?)\*", r"\1", text)  # RU: *курсив* → курсив
    text = re.sub(r"_(.+?)_", r"\1", text)  # RU: _курсив_ → курсив

    # Remove code blocks
    text = re.sub(
        r"```[\s\S]*?```", "", text
    )  # RU: многострочный блок кода удаляется целиком
    text = re.sub(r"`(.+?)`", r"\1", text)  # RU: `инлайн код` → инлайн код

    # Remove links
    text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)  # RU: [текст](url) → текст

    return text


def strip_html(text: str) -> str:
    """Remove HTML formatting from text.

    Args:
        text: Text with HTML

    Returns:
        Plain text
    """
    # RU: Удаляет HTML-теги регулярным выражением, затем декодирует HTML-сущности.
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)  # RU: <тег> и </тег> удаляются без остатка

    # Unescape HTML entities
    text = html.unescape(text)  # RU: &amp; → &, &lt; → < и т.д.

    return text


def get_args(text: str, max_split: int = -1) -> List[str]:
    """Extract arguments from command text.

    Args:
        text: Command text (e.g., ".echo hello world")
        max_split: Maximum number of splits (default -1 = no limit)

    Returns:
        List of arguments (excluding command)
    """
    # RU: Разбивает строку по пробелам и отбрасывает первый элемент (саму команду).
    parts = text.split(maxsplit=max_split + 1 if max_split > 0 else max_split)
    return parts[1:] if len(parts) > 1 else []


def format_bytes(size: int) -> str:
    """Format bytes as human-readable string.

    Args:
        size: Size in bytes

    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    # RU: Итерируется по единицам и делит на 1024 пока размер не уложится в текущую единицу.
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


def format_duration(seconds: float) -> str:
    """Format duration as human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string (e.g., "1h 23m 45s")
    """
    # RU: Последовательно извлекает дни, часы, минуты, секунды из общего числа секунд.
    if seconds < 60:
        return f"{seconds:.1f}s"

    minutes = int(seconds // 60)
    seconds = int(seconds % 60)

    if minutes < 60:
        return f"{minutes}m {seconds}s"

    hours = minutes // 60
    minutes = minutes % 60

    if hours < 24:
        return f"{hours}h {minutes}m {seconds}s"

    days = hours // 24
    hours = hours % 24

    return f"{days}d {hours}h {minutes}m {seconds}s"
