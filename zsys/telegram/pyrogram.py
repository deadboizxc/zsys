"""Pyrogram compatibility layer for zsys.telegram.

Provides PyrogramClient and PyrogramConfig as drop-in replacements
that use TDLib under the hood while maintaining Pyrogram API compatibility.

DEPRECATED: Use TdlibClient and TdlibConfig directly.
This module is kept for backwards compatibility with existing userbots.

Example::

    # New way (recommended)
    from zsys.telegram import TdlibClient, TdlibConfig

    # Old way (still works)
    from zsys.telegram.pyrogram import PyrogramClient, PyrogramConfig
"""
# RU: УСТАРЕЛО: используйте TdlibClient/TdlibConfig напрямую.

from __future__ import annotations

from typing import Any, Callable, Coroutine, List, Optional

from pydantic import Field

from zsys.telegram.client import TdlibClient
from zsys.telegram.config import TdlibConfig


class PyrogramConfig(TdlibConfig):
    """Pyrogram-compatible configuration extending TdlibConfig.

    Adds fields specific to zxc_userbot that don't exist in base TdlibConfig.
    """

    # Extended fields for zxc_userbot compatibility
    enable_api_server: bool = Field(default=False, description="Enable API server")
    enable_admin_bot: bool = Field(default=False, description="Enable admin bot")
    admin_bot_token: str = Field(default="", description="Admin bot token")
    enable_hot_reload: bool = Field(default=False, description="Hot reload modules")
    hot_reload_dirs: List[str] = Field(
        default_factory=lambda: ["modules", "custom_modules"]
    )

    class Config:
        env_prefix = "PYROGRAM_"


class PyrogramClient(TdlibClient):
    """Pyrogram-compatible client extending TdlibClient.

    Provides Pyrogram-like API while using TDLib under the hood.
    All zsys modules that expect Pyrogram Client methods will work.

    Note:
        This is a compatibility shim. For new code, use TdlibClient directly.
    """

    def __init__(
        self,
        config: PyrogramConfig,
        ask_phone: Optional[
            Callable[["PyrogramClient"], Coroutine[Any, Any, None]]
        ] = None,
        ask_code: Optional[
            Callable[["PyrogramClient"], Coroutine[Any, Any, None]]
        ] = None,
        ask_pass: Optional[
            Callable[["PyrogramClient"], Coroutine[Any, Any, None]]
        ] = None,
    ) -> None:
        super().__init__(config, ask_phone, ask_code, ask_pass)
        self._pyrogram_config = config
        self._api_server_task = None
        self._admin_bot_task = None
        self._hot_reload_task = None

    @property
    def enable_api_server(self) -> bool:
        return self._pyrogram_config.enable_api_server

    @property
    def enable_admin_bot(self) -> bool:
        return self._pyrogram_config.enable_admin_bot

    @property
    def admin_bot_token(self) -> str:
        return self._pyrogram_config.admin_bot_token

    @property
    def enable_hot_reload(self) -> bool:
        return self._pyrogram_config.enable_hot_reload

    @property
    def hot_reload_dirs(self) -> List[str]:
        return self._pyrogram_config.hot_reload_dirs

    # Pyrogram compatibility methods
    async def get_me(self) -> Any:
        """Get current user info (Pyrogram compatibility)."""
        return await self.get_current_user()

    async def send_message(
        self,
        chat_id: Any,
        text: str,
        parse_mode: Optional[str] = None,
        disable_notification: bool = False,
        reply_to_message_id: Optional[int] = None,
        **kwargs: Any,
    ) -> Any:
        """Send text message (Pyrogram-compatible signature)."""
        return await super().send_message(
            chat_id=chat_id,
            text=text,
            reply_to=reply_to_message_id,
            disable_notification=disable_notification,
        )

    async def edit_message_text(
        self,
        chat_id: Any,
        message_id: int,
        text: str,
        parse_mode: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        """Edit message text (Pyrogram-compatible signature)."""
        return await self.edit_message(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
        )

    async def delete_messages(
        self,
        chat_id: Any,
        message_ids: List[int],
        **kwargs: Any,
    ) -> int:
        """Delete messages (Pyrogram-compatible signature)."""
        count = 0
        for msg_id in message_ids:
            try:
                await self.delete_message(chat_id, msg_id)
                count += 1
            except Exception:
                pass
        return count

    async def get_chat(self, chat_id: Any) -> Any:
        """Get chat info (Pyrogram compatibility)."""
        return await super().get_chat(chat_id)

    async def get_users(self, user_ids: List[Any]) -> List[Any]:
        """Get users info (Pyrogram compatibility)."""
        users = []
        for uid in user_ids:
            try:
                users.append(await self.get_user(uid))
            except Exception:
                pass
        return users

    async def iter_chat_members(
        self, chat_id: Any, limit: int = 0, **kwargs: Any
    ) -> Any:
        """Iterate chat members (Pyrogram compatibility)."""
        members = await self.get_chat_members(chat_id, limit=limit or 200)
        for m in members:
            yield m

    async def get_chat_members_count(self, chat_id: Any) -> int:
        """Get chat members count (Pyrogram compatibility)."""
        chat = await self.get_chat(chat_id)
        return getattr(chat, "member_count", 0)


__all__ = ["PyrogramClient", "PyrogramConfig"]
