"""
Message formatting utilities for Telegram bots.

Provides helpers for formatting text with HTML/Markdown.
"""

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
    return html.escape(text)


def format_bold(text: str, escape: bool = True) -> str:
    """Format text as bold.
    
    Args:
        text: Text to format
        escape: Whether to escape HTML (default True)
        
    Returns:
        Bold-formatted text
    """
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
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def split_text(text: str, max_length: int = 4096) -> List[str]:
    """Split text into chunks for Telegram messages.
    
    Args:
        text: Text to split
        max_length: Maximum chunk length (default 4096)
        
    Returns:
        List of text chunks
    """
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    current_chunk = ""
    
    for line in text.split('\n'):
        if len(current_chunk) + len(line) + 1 <= max_length:
            current_chunk += line + '\n'
        else:
            if current_chunk:
                chunks.append(current_chunk)
            
            # If single line is too long, split it
            if len(line) > max_length:
                for i in range(0, len(line), max_length):
                    chunks.append(line[i:i + max_length])
                current_chunk = ""
            else:
                current_chunk = line + '\n'
    
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
    # Remove bold/italic
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'_(.+?)_', r'\1', text)
    
    # Remove code blocks
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`(.+?)`', r'\1', text)
    
    # Remove links
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
    
    return text


def strip_html(text: str) -> str:
    """Remove HTML formatting from text.
    
    Args:
        text: Text with HTML
        
    Returns:
        Plain text
    """
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Unescape HTML entities
    text = html.unescape(text)
    
    return text


def get_args(text: str, max_split: int = -1) -> List[str]:
    """Extract arguments from command text.
    
    Args:
        text: Command text (e.g., ".echo hello world")
        max_split: Maximum number of splits (default -1 = no limit)
        
    Returns:
        List of arguments (excluding command)
    """
    parts = text.split(maxsplit=max_split + 1 if max_split > 0 else max_split)
    return parts[1:] if len(parts) > 1 else []


def format_bytes(size: int) -> str:
    """Format bytes as human-readable string.
    
    Args:
        size: Size in bytes
        
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
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
