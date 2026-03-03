"""
Core Message Tools Module - Text formatting and message utilities.

Provides:
- Text formatting (bold, italic, code, etc.)
- Time/date utilities
- Hashing functions
- Rate limiting
- Long message splitting
"""

import time
import hashlib
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Union, Any, Callable, TypeVar

# Type for message objects (Pyrogram, Telethon, etc.)
MessageType = TypeVar("MessageType")

__all__ = [
    # Text formatting
    "bold",
    "italic",
    "underline",
    "strikethrough",
    "code",
    "preformatted",
    "spoiler",
    "link",
    "mention",
    # Time utilities
    "timestamp_to_date",
    "date_to_timestamp",
    "human_time",
    "current_timestamp",
    "time_difference",
    # Hashing
    "md5_hash",
    "sha256_hash",
    "sha512_hash",
    "hash_file",
    # Rate limiting
    "rate_limit",
    "clear_rate_limits",
    # Message utilities
    "split_text",
    "escape_html",
    "strip_html",
]


# =============================================================================
# TEXT FORMATTING (HTML)
# =============================================================================


def bold(text: str) -> str:
    """Wrap text in bold tags."""
    return f"<b>{text}</b>"


def italic(text: str) -> str:
    """Wrap text in italic tags."""
    return f"<i>{text}</i>"


def underline(text: str) -> str:
    """Wrap text in underline tags."""
    return f"<u>{text}</u>"


def strikethrough(text: str) -> str:
    """Wrap text in strikethrough tags."""
    return f"<s>{text}</s>"


def code(text: str) -> str:
    """Wrap text in inline code tags."""
    return f"<code>{text}</code>"


def preformatted(text: str, language: str = "") -> str:
    """Wrap text in preformatted code block."""
    if language:
        return f'<pre language="{language}">{text}</pre>'
    return f"<pre>{text}</pre>"


def spoiler(text: str) -> str:
    """Wrap text in spoiler tags."""
    return f"<tg-spoiler>{text}</tg-spoiler>"


def link(text: str, url: str) -> str:
    """Create hyperlink."""
    return f'<a href="{url}">{text}</a>'


def mention(text: str, user_id: int) -> str:
    """Create user mention link."""
    return f'<a href="tg://user?id={user_id}">{text}</a>'


# =============================================================================
# TIME / DATE UTILITIES
# =============================================================================


def timestamp_to_date(timestamp: int, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Convert Unix timestamp to formatted date string."""
    return datetime.utcfromtimestamp(timestamp).strftime(fmt)


def date_to_timestamp(date_str: str, fmt: str = "%Y-%m-%d %H:%M:%S") -> int:
    """Convert date string to Unix timestamp."""
    return int(datetime.strptime(date_str, fmt).timestamp())


def human_time(seconds: int, short: bool = False) -> str:
    """
    Convert seconds to human-readable time string.

    Args:
        seconds: Number of seconds
        short: Use short format (d, h, m, s)

    Returns:
        Human-readable time string
    """
    delta = timedelta(seconds=abs(seconds))
    parts = []

    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, secs = divmod(remainder, 60)

    if short:
        if days:
            parts.append(f"{days}d")
        if hours:
            parts.append(f"{hours}h")
        if minutes:
            parts.append(f"{minutes}m")
        if secs:
            parts.append(f"{secs}s")
    else:
        if days:
            parts.append(f"{days} дн.")
        if hours:
            parts.append(f"{hours} ч.")
        if minutes:
            parts.append(f"{minutes} мин.")
        if secs:
            parts.append(f"{secs} сек.")

    return " ".join(parts) or ("0s" if short else "0 сек.")


def current_timestamp() -> int:
    """Get current Unix timestamp."""
    return int(time.time())


def time_difference(timestamp1: int, timestamp2: int) -> int:
    """Get absolute difference between two timestamps."""
    return abs(timestamp1 - timestamp2)


# =============================================================================
# HASHING
# =============================================================================


def md5_hash(text: str) -> str:
    """Calculate MD5 hash of text."""
    return hashlib.md5(text.encode()).hexdigest()


def sha256_hash(text: str) -> str:
    """Calculate SHA256 hash of text."""
    return hashlib.sha256(text.encode()).hexdigest()


def sha512_hash(text: str) -> str:
    """Calculate SHA512 hash of text."""
    return hashlib.sha512(text.encode()).hexdigest()


async def hash_file(file_path: str, algo: str = "sha256") -> str:
    """
    Calculate hash of file contents.

    Args:
        file_path: Path to file
        algo: Hash algorithm (md5, sha256, sha512)

    Returns:
        Hex digest of file hash
    """
    hash_funcs = {
        "md5": hashlib.md5,
        "sha256": hashlib.sha256,
        "sha512": hashlib.sha512,
    }
    hash_func = hash_funcs.get(algo, hashlib.sha256)()

    try:
        import aiofiles

        async with aiofiles.open(file_path, "rb") as f:
            while chunk := await f.read(4096):
                hash_func.update(chunk)
    except ImportError:
        # Fallback to sync
        with open(file_path, "rb") as f:
            while chunk := f.read(4096):
                hash_func.update(chunk)

    return hash_func.hexdigest()


# =============================================================================
# RATE LIMITING
# =============================================================================

_rate_limits: dict = {}


def rate_limit(key: Union[int, str], delay: float = 5.0) -> bool:
    """
    Simple rate limiter.

    Args:
        key: Unique key for rate limiting (e.g., user_id)
        delay: Minimum delay between actions in seconds

    Returns:
        True if action allowed, False if rate limited
    """
    now = time.time()
    if key in _rate_limits and now - _rate_limits[key] < delay:
        return False
    _rate_limits[key] = now
    return True


def clear_rate_limits() -> None:
    """Clear all rate limit records."""
    global _rate_limits
    _rate_limits.clear()


# =============================================================================
# MESSAGE UTILITIES
# =============================================================================


def escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def strip_html(text: str) -> str:
    """Remove HTML tags from text."""
    import re

    return re.sub(r"<[^>]+>", "", text)


def split_text(
    text: str, max_length: int = 4096, preserve_lines: bool = True
) -> List[str]:
    """
    Split long text into chunks.

    Args:
        text: Text to split
        max_length: Maximum length of each chunk (1-4096)
        preserve_lines: Try not to split in the middle of lines

    Returns:
        List of text chunks
    """
    max_length = max(1, min(max_length, 4096))

    if len(text) <= max_length:
        return [text]

    if preserve_lines:
        parts = []
        current_part = ""

        for line in text.split("\n"):
            if len(current_part) + len(line) + 1 > max_length:
                if current_part:
                    parts.append(current_part)
                    current_part = line
                else:
                    # Line itself is too long, split it
                    parts.extend(
                        [
                            line[i : i + max_length]
                            for i in range(0, len(line), max_length)
                        ]
                    )
            else:
                current_part = f"{current_part}\n{line}" if current_part else line

        if current_part:
            parts.append(current_part)

        return parts
    else:
        return [text[i : i + max_length] for i in range(0, len(text), max_length)]
