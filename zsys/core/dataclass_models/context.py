"""
Base context classes for unified module system.

This module provides the abstract base classes and common types
that all platform-specific contexts inherit from.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional, Union, List, BinaryIO, Callable, Awaitable
from pathlib import Path


@dataclass
class User:
    """Unified user representation."""
    id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_bot: bool = False
    language_code: Optional[str] = None
    is_premium: bool = False
    
    @property
    def full_name(self) -> str:
        """Full name (first + last)."""
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or ""
    
    @property
    def mention(self) -> str:
        """Markdown mention link."""
        if self.username:
            return f"@{self.username}"
        return f"[{self.full_name}](tg://user?id={self.id})"
    
    @property
    def html_mention(self) -> str:
        """HTML mention link."""
        if self.username:
            return f"@{self.username}"
        return f'<a href="tg://user?id={self.id}">{self.full_name}</a>'


@dataclass
class Chat:
    """Unified chat representation."""
    id: int
    type: str  # "private", "group", "supergroup", "channel"
    title: Optional[str] = None
    username: Optional[str] = None
    description: Optional[str] = None
    members_count: Optional[int] = None
    
    @property
    def is_private(self) -> bool:
        return self.type == "private"
    
    @property
    def is_group(self) -> bool:
        return self.type in ("group", "supergroup")
    
    @property
    def is_channel(self) -> bool:
        return self.type == "channel"
    
    @property
    def link(self) -> Optional[str]:
        """Get chat link if available."""
        if self.username:
            return f"https://t.me/{self.username}"
        return None


@dataclass
class Context(ABC):
    """
    Abstract base context for command handlers.
    
    Provides a consistent interface regardless of the underlying platform.
    All platform-specific contexts (Pyrogram, aiogram, telebot) inherit from this.
    
    Usage:
        @command("hello")
        async def hello_cmd(ctx: Context):
            await ctx.reply(f"Hello, {ctx.user.first_name}!")
            
            # Access platform-specific features
            if ctx.platform == "pyrogram":
                # Pyrogram-specific code
                await ctx.raw.forward(chat_id)
    """
    
    # Core attributes (set by subclasses)
    raw: Any = None  # Original message object
    client: Any = None  # Original client object
    
    # Parsed command data
    command: str = ""
    args: List[str] = field(default_factory=list)
    text: str = ""
    
    # Platform info
    platform: str = "unknown"  # "pyrogram", "aiogram", "telebot", "api"
    
    # ==========================================================================
    # PROPERTIES
    # ==========================================================================
    
    @property
    @abstractmethod
    def user(self) -> User:
        """Get the user who sent the message."""
        pass
    
    @property
    @abstractmethod
    def chat(self) -> Chat:
        """Get the chat where the message was sent."""
        pass
    
    @property
    @abstractmethod
    def message_id(self) -> int:
        """Get the message ID."""
        pass
    
    @property
    def arg(self) -> str:
        """Get all arguments as a single string."""
        return " ".join(self.args)
    
    @property
    def has_args(self) -> bool:
        """Check if command has arguments."""
        return len(self.args) > 0
    
    @property
    def is_reply(self) -> bool:
        """Check if message is a reply."""
        return False  # Override in subclasses
    
    @property
    def is_private(self) -> bool:
        """Check if in private chat."""
        return self.chat.is_private
    
    @property
    def is_group(self) -> bool:
        """Check if in group chat."""
        return self.chat.is_group
    
    # ==========================================================================
    # ABSTRACT METHODS - Must be implemented
    # ==========================================================================
    
    @abstractmethod
    async def reply(
        self,
        text: str,
        parse_mode: Optional[str] = "markdown",
        disable_preview: bool = True,
        **kwargs
    ) -> Any:
        """Reply to the message."""
        pass
    
    @abstractmethod
    async def edit(
        self,
        text: str,
        parse_mode: Optional[str] = "markdown",
        disable_preview: bool = True,
        **kwargs
    ) -> Any:
        """Edit the original message (if possible)."""
        pass
    
    @abstractmethod
    async def delete(self) -> bool:
        """Delete the original message."""
        pass
    
    @abstractmethod
    async def send_photo(
        self,
        photo: Union[str, Path, BinaryIO],
        caption: Optional[str] = None,
        **kwargs
    ) -> Any:
        """Send a photo."""
        pass
    
    @abstractmethod
    async def send_document(
        self,
        document: Union[str, Path, BinaryIO],
        caption: Optional[str] = None,
        **kwargs
    ) -> Any:
        """Send a document."""
        pass
    
    @abstractmethod
    async def send_video(
        self,
        video: Union[str, Path, BinaryIO],
        caption: Optional[str] = None,
        **kwargs
    ) -> Any:
        """Send a video."""
        pass
    
    @abstractmethod
    async def send_sticker(
        self,
        sticker: Union[str, BinaryIO],
        **kwargs
    ) -> Any:
        """Send a sticker."""
        pass
    
    # ==========================================================================
    # COMMON METHODS - Default implementations
    # ==========================================================================
    
    async def answer(
        self,
        text: str,
        parse_mode: Optional[str] = "markdown",
        **kwargs
    ) -> Any:
        """
        Smart answer - edit if userbot, reply if bot.
        Override in platform-specific implementations.
        """
        try:
            return await self.edit(text, parse_mode=parse_mode, **kwargs)
        except Exception:
            return await self.reply(text, parse_mode=parse_mode, **kwargs)
    
    async def send(
        self,
        text: str,
        parse_mode: Optional[str] = "markdown",
        **kwargs
    ) -> Any:
        """Send a new message to the chat (not reply)."""
        return await self.reply(text, parse_mode=parse_mode, **kwargs)
    
    async def react(self, emoji: str) -> bool:
        """Add reaction to message. Override if platform supports it."""
        return False
    
    async def get_reply_message(self) -> Optional["Context"]:
        """Get the message being replied to. Override in implementations."""
        return None
    
    async def download_media(self, path: Optional[str] = None) -> Optional[str]:
        """Download media from message. Override in implementations."""
        return None
    
    async def forward(self, chat_id: int) -> Any:
        """Forward message to another chat. Override in implementations."""
        raise NotImplementedError("forward not supported on this platform")
    
    async def copy(self, chat_id: int) -> Any:
        """Copy message to another chat. Override in implementations."""
        raise NotImplementedError("copy not supported on this platform")
    
    async def pin(self, disable_notification: bool = False) -> bool:
        """Pin the message. Override in implementations."""
        return False
    
    async def unpin(self) -> bool:
        """Unpin the message. Override in implementations."""
        return False
    
    # ==========================================================================
    # UTILITY METHODS
    # ==========================================================================
    
    def get_arg(self, index: int, default: str = "") -> str:
        """Get argument by index safely."""
        if index < len(self.args):
            return self.args[index]
        return default
    
    def get_args_after(self, index: int) -> str:
        """Get all arguments after index as string."""
        if index < len(self.args):
            return " ".join(self.args[index:])
        return ""
    
    def require_args(self, min_count: int = 1) -> bool:
        """Check if minimum number of arguments provided."""
        return len(self.args) >= min_count
    
    async def require_reply(self) -> Optional["Context"]:
        """
        Get reply message or None.
        
        Usage:
            reply = await ctx.require_reply()
            if not reply:
                return await ctx.reply("Reply to a message!")
        """
        return await self.get_reply_message()
