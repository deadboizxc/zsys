"""
Pyrogram context adapter with full feature support.

Supports all Pyrogram features:
- Message editing, forwarding, copying
- Media download/upload
- Reactions
- Reply markup (inline keyboards)
- Chat actions (typing, uploading...)
- User/chat info fetching
- And more!
"""

from __future__ import annotations

from typing import Any, Optional, Union, List, BinaryIO, TYPE_CHECKING
from pathlib import Path

from zsys.core.dataclass_models.context import Context, User, Chat

if TYPE_CHECKING:
    from pyrogram import Client
    from pyrogram.types import Message, InlineKeyboardMarkup, ReplyKeyboardMarkup


class PyrogramContext(Context):
    """
    Full-featured Pyrogram context.
    
    Provides all Pyrogram capabilities through the unified interface,
    plus direct access to raw Pyrogram objects for advanced usage.
    
    Usage:
        @command("example")
        async def example(ctx: PyrogramContext):
            # Unified API
            await ctx.reply("Hello!")
            
            # Pyrogram-specific
            await ctx.typing()  # Show typing action
            await ctx.forward(chat_id)  # Forward message
            
            # Direct access to Pyrogram
            await ctx.raw.react("👍")  # Use raw Message methods
    """
    
    platform: str = "pyrogram"
    
    def __init__(
        self,
        client: "Client",
        message: "Message",
        command: str = "",
        args: List[str] = None
    ):
        self.client = client
        self.raw = message
        self.command = command
        self.args = args or []
        self.text = message.text or message.caption or ""
        self._user: Optional[User] = None
        self._chat: Optional[Chat] = None
    
    # ==========================================================================
    # PROPERTIES
    # ==========================================================================
    
    @property
    def user(self) -> User:
        if self._user is None:
            u = self.raw.from_user
            if not u:
                self._user = User(id=0)
            else:
                self._user = User(
                    id=u.id,
                    username=u.username,
                    first_name=u.first_name,
                    last_name=u.last_name,
                    is_bot=u.is_bot,
                    language_code=u.language_code,
                    is_premium=getattr(u, 'is_premium', False),
                )
        return self._user
    
    @property
    def chat(self) -> Chat:
        if self._chat is None:
            c = self.raw.chat
            chat_type = c.type.value if hasattr(c.type, 'value') else str(c.type)
            self._chat = Chat(
                id=c.id,
                type=chat_type,
                title=c.title,
                username=c.username,
                description=getattr(c, 'description', None),
                members_count=getattr(c, 'members_count', None),
            )
        return self._chat
    
    @property
    def message_id(self) -> int:
        return self.raw.id
    
    @property
    def is_reply(self) -> bool:
        return self.raw.reply_to_message is not None
    
    @property
    def is_self(self) -> bool:
        """Check if message is from the userbot owner."""
        return self.raw.from_user and self.raw.from_user.is_self
    
    @property
    def has_media(self) -> bool:
        """Check if message has any media."""
        return self.raw.media is not None
    
    @property
    def media_type(self) -> Optional[str]:
        """Get media type if present."""
        if self.raw.media:
            return self.raw.media.value if hasattr(self.raw.media, 'value') else str(self.raw.media)
        return None
    
    # ==========================================================================
    # CORE METHODS
    # ==========================================================================
    
    def _parse_mode(self, mode: Optional[str]):
        """Convert string parse mode to Pyrogram enum."""
        from pyrogram.enums import ParseMode
        if mode == "markdown":
            return ParseMode.MARKDOWN
        elif mode == "html":
            return ParseMode.HTML
        return ParseMode.DISABLED
    
    async def reply(
        self,
        text: str,
        parse_mode: Optional[str] = "markdown",
        disable_preview: bool = True,
        reply_markup: Optional["InlineKeyboardMarkup"] = None,
        **kwargs
    ) -> "Message":
        """Reply to the message."""
        # Убираем дубли: если caller передал disable_web_page_preview в kwargs — используем его
        disable_preview = kwargs.pop("disable_web_page_preview", disable_preview)
        return await self.raw.reply(
            text,
            parse_mode=self._parse_mode(parse_mode),
            disable_web_page_preview=disable_preview,
            reply_markup=reply_markup,
            **kwargs
        )
    
    async def edit(
        self,
        text: str,
        parse_mode: Optional[str] = "markdown",
        disable_preview: bool = True,
        reply_markup: Optional["InlineKeyboardMarkup"] = None,
        **kwargs
    ) -> "Message":
        """Edit the message."""
        # Убираем дубли: если caller передал disable_web_page_preview в kwargs — используем его
        disable_preview = kwargs.pop("disable_web_page_preview", disable_preview)
        return await self.raw.edit_text(
            text,
            parse_mode=self._parse_mode(parse_mode),
            disable_web_page_preview=disable_preview,
            reply_markup=reply_markup,
            **kwargs
        )
    
    async def delete(self, revoke: bool = True) -> bool:
        """Delete the message."""
        try:
            await self.raw.delete(revoke=revoke)
            return True
        except Exception:
            return False
    
    async def answer(
        self,
        text: str,
        parse_mode: Optional[str] = "markdown",
        **kwargs
    ) -> "Message":
        """Smart answer - edit if own message, reply otherwise."""
        if self.is_self:
            return await self.edit(text, parse_mode=parse_mode, **kwargs)
        return await self.reply(text, parse_mode=parse_mode, **kwargs)
    
    # ==========================================================================
    # MEDIA METHODS
    # ==========================================================================
    
    async def send_photo(
        self,
        photo: Union[str, Path, BinaryIO],
        caption: Optional[str] = None,
        parse_mode: Optional[str] = "markdown",
        reply_markup: Optional["InlineKeyboardMarkup"] = None,
        spoiler: bool = False,
        **kwargs
    ) -> "Message":
        """Send a photo."""
        return await self.raw.reply_photo(
            photo,
            caption=caption,
            parse_mode=self._parse_mode(parse_mode),
            reply_markup=reply_markup,
            has_spoiler=spoiler,
            **kwargs
        )
    
    async def send_document(
        self,
        document: Union[str, Path, BinaryIO],
        caption: Optional[str] = None,
        parse_mode: Optional[str] = "markdown",
        thumb: Optional[str] = None,
        **kwargs
    ) -> "Message":
        """Send a document."""
        return await self.raw.reply_document(
            document,
            caption=caption,
            parse_mode=self._parse_mode(parse_mode),
            thumb=thumb,
            **kwargs
        )
    
    async def send_video(
        self,
        video: Union[str, Path, BinaryIO],
        caption: Optional[str] = None,
        parse_mode: Optional[str] = "markdown",
        duration: int = 0,
        width: int = 0,
        height: int = 0,
        thumb: Optional[str] = None,
        spoiler: bool = False,
        **kwargs
    ) -> "Message":
        """Send a video."""
        return await self.raw.reply_video(
            video,
            caption=caption,
            parse_mode=self._parse_mode(parse_mode),
            duration=duration,
            width=width,
            height=height,
            thumb=thumb,
            has_spoiler=spoiler,
            **kwargs
        )
    
    async def send_audio(
        self,
        audio: Union[str, Path, BinaryIO],
        caption: Optional[str] = None,
        duration: int = 0,
        performer: Optional[str] = None,
        title: Optional[str] = None,
        **kwargs
    ) -> "Message":
        """Send an audio file."""
        return await self.raw.reply_audio(
            audio,
            caption=caption,
            duration=duration,
            performer=performer,
            title=title,
            **kwargs
        )
    
    async def send_voice(
        self,
        voice: Union[str, Path, BinaryIO],
        caption: Optional[str] = None,
        duration: int = 0,
        **kwargs
    ) -> "Message":
        """Send a voice message."""
        return await self.raw.reply_voice(
            voice,
            caption=caption,
            duration=duration,
            **kwargs
        )
    
    async def send_video_note(
        self,
        video_note: Union[str, Path, BinaryIO],
        duration: int = 0,
        length: int = 1,
        **kwargs
    ) -> "Message":
        """Send a video note (round video)."""
        return await self.raw.reply_video_note(
            video_note,
            duration=duration,
            length=length,
            **kwargs
        )
    
    async def send_sticker(
        self,
        sticker: Union[str, BinaryIO],
        **kwargs
    ) -> "Message":
        """Send a sticker."""
        return await self.raw.reply_sticker(sticker, **kwargs)
    
    async def send_animation(
        self,
        animation: Union[str, Path, BinaryIO],
        caption: Optional[str] = None,
        **kwargs
    ) -> "Message":
        """Send a GIF/animation."""
        return await self.raw.reply_animation(animation, caption=caption, **kwargs)
    
    async def send_media_group(
        self,
        media: List[Any],
        **kwargs
    ) -> List["Message"]:
        """Send a media group (album)."""
        return await self.client.send_media_group(
            self.chat.id,
            media,
            reply_to_message_id=self.message_id,
            **kwargs
        )
    
    # ==========================================================================
    # MESSAGE OPERATIONS
    # ==========================================================================
    
    async def forward(self, chat_id: int, disable_notification: bool = False) -> "Message":
        """Forward the message to another chat."""
        return await self.raw.forward(chat_id, disable_notification=disable_notification)
    
    async def copy(
        self,
        chat_id: int,
        caption: Optional[str] = None,
        **kwargs
    ) -> "Message":
        """Copy the message to another chat."""
        return await self.raw.copy(chat_id, caption=caption, **kwargs)
    
    async def pin(self, disable_notification: bool = False, both_sides: bool = False) -> bool:
        """Pin the message."""
        try:
            await self.raw.pin(disable_notification=disable_notification, both_sides=both_sides)
            return True
        except Exception:
            return False
    
    async def unpin(self) -> bool:
        """Unpin the message."""
        try:
            await self.raw.unpin()
            return True
        except Exception:
            return False
    
    async def react(self, emoji: str) -> bool:
        """Add reaction to the message."""
        try:
            await self.raw.react(emoji)
            return True
        except Exception:
            return False
    
    # ==========================================================================
    # REPLY MESSAGE
    # ==========================================================================
    
    async def get_reply_message(self) -> Optional["PyrogramContext"]:
        """Get the message being replied to."""
        if self.raw.reply_to_message:
            return PyrogramContext(
                self.client,
                self.raw.reply_to_message,
                command="",
                args=[]
            )
        return None
    
    async def get_reply_or_self(self) -> "PyrogramContext":
        """Get reply message or self if not replying."""
        reply = await self.get_reply_message()
        return reply or self
    
    # ==========================================================================
    # MEDIA DOWNLOAD
    # ==========================================================================
    
    async def download_media(
        self,
        path: Optional[str] = None,
        progress: Optional[callable] = None
    ) -> Optional[str]:
        """Download media from the message."""
        if not self.raw.media:
            return None
        return await self.raw.download(file_name=path, progress=progress)
    
    # ==========================================================================
    # CHAT ACTIONS
    # ==========================================================================
    
    async def typing(self):
        """Send 'typing' action."""
        from pyrogram.enums import ChatAction
        await self.client.send_chat_action(self.chat.id, ChatAction.TYPING)
    
    async def upload_photo(self):
        """Send 'uploading photo' action."""
        from pyrogram.enums import ChatAction
        await self.client.send_chat_action(self.chat.id, ChatAction.UPLOAD_PHOTO)
    
    async def upload_video(self):
        """Send 'uploading video' action."""
        from pyrogram.enums import ChatAction
        await self.client.send_chat_action(self.chat.id, ChatAction.UPLOAD_VIDEO)
    
    async def upload_document(self):
        """Send 'uploading document' action."""
        from pyrogram.enums import ChatAction
        await self.client.send_chat_action(self.chat.id, ChatAction.UPLOAD_DOCUMENT)
    
    async def record_voice(self):
        """Send 'recording voice' action."""
        from pyrogram.enums import ChatAction
        await self.client.send_chat_action(self.chat.id, ChatAction.RECORD_VOICE)
    
    async def record_video(self):
        """Send 'recording video' action."""
        from pyrogram.enums import ChatAction
        await self.client.send_chat_action(self.chat.id, ChatAction.RECORD_VIDEO)
    
    async def cancel_action(self):
        """Cancel any chat action."""
        from pyrogram.enums import ChatAction
        await self.client.send_chat_action(self.chat.id, ChatAction.CANCEL)
    
    # ==========================================================================
    # USER/CHAT INFO
    # ==========================================================================
    
    async def get_user_info(self, user_id: Optional[int] = None) -> Any:
        """Get full user info."""
        uid = user_id or self.user.id
        return await self.client.get_users(uid)
    
    async def get_chat_info(self, chat_id: Optional[int] = None) -> Any:
        """Get full chat info."""
        cid = chat_id or self.chat.id
        return await self.client.get_chat(cid)
    
    async def get_chat_member(self, user_id: Optional[int] = None) -> Any:
        """Get chat member info."""
        uid = user_id or self.user.id
        return await self.client.get_chat_member(self.chat.id, uid)
    
    async def is_admin(self, user_id: Optional[int] = None) -> bool:
        """Check if user is admin in current chat."""
        if self.is_private:
            return True
        try:
            member = await self.get_chat_member(user_id)
            from pyrogram.enums import ChatMemberStatus
            return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)
        except Exception:
            return False
    
    async def is_owner(self, user_id: Optional[int] = None) -> bool:
        """Check if user is owner of current chat."""
        if self.is_private:
            return True
        try:
            member = await self.get_chat_member(user_id)
            from pyrogram.enums import ChatMemberStatus
            return member.status == ChatMemberStatus.OWNER
        except Exception:
            return False
    
    # ==========================================================================
    # MODERATION
    # ==========================================================================
    
    async def ban_user(self, user_id: Optional[int] = None) -> bool:
        """Ban user from chat."""
        try:
            uid = user_id or self.user.id
            await self.client.ban_chat_member(self.chat.id, uid)
            return True
        except Exception:
            return False
    
    async def unban_user(self, user_id: Optional[int] = None) -> bool:
        """Unban user from chat."""
        try:
            uid = user_id or self.user.id
            await self.client.unban_chat_member(self.chat.id, uid)
            return True
        except Exception:
            return False
    
    async def kick_user(self, user_id: Optional[int] = None) -> bool:
        """Kick user from chat (ban + unban)."""
        uid = user_id or self.user.id
        if await self.ban_user(uid):
            return await self.unban_user(uid)
        return False
    
    async def mute_user(
        self,
        user_id: Optional[int] = None,
        until_date: int = 0
    ) -> bool:
        """Mute user in chat."""
        try:
            from pyrogram.types import ChatPermissions
            uid = user_id or self.user.id
            await self.client.restrict_chat_member(
                self.chat.id,
                uid,
                ChatPermissions(),
                until_date=until_date
            )
            return True
        except Exception:
            return False
    
    async def unmute_user(self, user_id: Optional[int] = None) -> bool:
        """Unmute user in chat."""
        try:
            from pyrogram.types import ChatPermissions
            uid = user_id or self.user.id
            await self.client.restrict_chat_member(
                self.chat.id,
                uid,
                ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True
                )
            )
            return True
        except Exception:
            return False
    
    # ==========================================================================
    # INLINE KEYBOARDS
    # ==========================================================================
    
    @staticmethod
    def button(text: str, callback_data: str = None, url: str = None):
        """Create an inline button."""
        from pyrogram.types import InlineKeyboardButton
        if url:
            return InlineKeyboardButton(text, url=url)
        return InlineKeyboardButton(text, callback_data=callback_data or text)
    
    @staticmethod
    def keyboard(*rows: List):
        """Create an inline keyboard from rows of buttons."""
        from pyrogram.types import InlineKeyboardMarkup
        return InlineKeyboardMarkup([list(row) for row in rows])
    
    # ==========================================================================
    # INLINE QUERIES (for callback handling)
    # ==========================================================================
    
    async def answer_callback(self, text: str = "", show_alert: bool = False) -> bool:
        """Answer callback query (if this is a callback)."""
        if hasattr(self.raw, 'answer'):
            try:
                await self.raw.answer(text, show_alert=show_alert)
                return True
            except Exception:
                pass
        return False
