"""
TelegramContext — unified context adapter for zsys.telegram (TDLib-based).

Replaces platform-specific adapters (pyrogram, aiogram, telebot) with
a single implementation built on zsys.telegram.TdlibClient.

Usage:
    from zsys.telegram import TdlibClient, TdlibConfig
    from zsys.modules.context import TelegramContext

    client = TdlibClient(config)

    @client.on_message(filters.command("start"))
    async def start_handler(message):
        ctx = TelegramContext(client, message)
        await ctx.reply("Hello!")
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, BinaryIO, List, Optional, Union

from zsys.core.dataclass_models.context import Chat, Context, User

if TYPE_CHECKING:
    from zsys.telegram.client import TdlibClient
    from zsys.telegram.types import Message


class TelegramContext(Context):
    """
    Unified Telegram context built on zsys.telegram (TDLib).

    Provides full feature parity with Pyrogram/aiogram/telebot adapters
    but uses native TDLib implementation.

    Features:
    - Message operations (reply, edit, delete, forward, copy, pin)
    - Media sending (photo, video, document, audio, voice, sticker)
    - Chat actions (typing, uploading)
    - User/chat info
    - Moderation (ban, kick, mute)
    - Inline keyboards
    - Reactions
    """

    platform: str = "tdlib"

    def __init__(
        self,
        client: "TdlibClient",
        message: "Message",
        command: str = "",
        args: List[str] = None,
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
                    language_code=getattr(u, "language_code", None),
                    is_premium=getattr(u, "is_premium", False),
                )
        return self._user

    @property
    def chat(self) -> Chat:
        if self._chat is None:
            c = self.raw.chat
            chat_type = c.type if isinstance(c.type, str) else str(c.type)
            self._chat = Chat(
                id=c.id,
                type=chat_type,
                title=c.title,
                username=getattr(c, "username", None),
                description=getattr(c, "description", None),
                members_count=getattr(c, "members_count", None),
            )
        return self._chat

    @property
    def message_id(self) -> int:
        return self.raw.id

    @property
    def is_reply(self) -> bool:
        return self.raw.reply_to_message_id is not None and self.raw.reply_to_message_id > 0

    @property
    def is_self(self) -> bool:
        """Check if message is from the userbot owner."""
        me = getattr(self.client, "_me", None)
        return me is not None and self.user.id == me.id

    @property
    def has_media(self) -> bool:
        """Check if message has any media."""
        return self.raw.media_type is not None

    @property
    def media_type(self) -> Optional[str]:
        """Get media type if present."""
        return self.raw.media_type

    # ==========================================================================
    # CORE METHODS
    # ==========================================================================

    async def reply(
        self,
        text: str,
        parse_mode: Optional[str] = "markdown",
        disable_preview: bool = True,
        reply_markup: Any = None,
        **kwargs,
    ) -> "Message":
        """Reply to the message."""
        return await self.client.send_message(
            chat_id=self.chat.id,
            text=text,
            parse_mode=parse_mode,
            disable_web_page_preview=disable_preview,
            reply_to_message_id=self.message_id,
            reply_markup=reply_markup,
            **kwargs,
        )

    async def edit(
        self,
        text: str,
        parse_mode: Optional[str] = "markdown",
        disable_preview: bool = True,
        reply_markup: Any = None,
        **kwargs,
    ) -> "Message":
        """Edit the message."""
        return await self.client.edit_message_text(
            chat_id=self.chat.id,
            message_id=self.message_id,
            text=text,
            parse_mode=parse_mode,
            disable_web_page_preview=disable_preview,
            reply_markup=reply_markup,
            **kwargs,
        )

    async def delete(self, revoke: bool = True) -> bool:
        """Delete the message."""
        try:
            await self.client.delete_messages(
                chat_id=self.chat.id,
                message_ids=[self.message_id],
                revoke=revoke,
            )
            return True
        except Exception:
            return False

    async def answer(
        self, text: str, parse_mode: Optional[str] = "markdown", **kwargs
    ) -> "Message":
        """Smart answer - edit if own message, reply otherwise."""
        if self.is_self:
            return await self.edit(text, parse_mode=parse_mode, **kwargs)
        return await self.reply(text, parse_mode=parse_mode, **kwargs)

    async def send(
        self,
        text: str,
        parse_mode: Optional[str] = "markdown",
        reply_markup: Any = None,
        **kwargs,
    ) -> "Message":
        """Send a new message (not reply)."""
        return await self.client.send_message(
            chat_id=self.chat.id,
            text=text,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
            **kwargs,
        )

    # ==========================================================================
    # MEDIA METHODS
    # ==========================================================================

    async def send_photo(
        self,
        photo: Union[str, Path, BinaryIO],
        caption: Optional[str] = None,
        parse_mode: Optional[str] = "markdown",
        reply_markup: Any = None,
        spoiler: bool = False,
        **kwargs,
    ) -> "Message":
        """Send a photo."""
        return await self.client.send_photo(
            chat_id=self.chat.id,
            photo=str(photo) if isinstance(photo, Path) else photo,
            caption=caption,
            parse_mode=parse_mode,
            reply_to_message_id=self.message_id,
            reply_markup=reply_markup,
            has_spoiler=spoiler,
            **kwargs,
        )

    async def send_document(
        self,
        document: Union[str, Path, BinaryIO],
        caption: Optional[str] = None,
        parse_mode: Optional[str] = "markdown",
        thumb: Optional[str] = None,
        **kwargs,
    ) -> "Message":
        """Send a document."""
        return await self.client.send_document(
            chat_id=self.chat.id,
            document=str(document) if isinstance(document, Path) else document,
            caption=caption,
            parse_mode=parse_mode,
            reply_to_message_id=self.message_id,
            thumb=thumb,
            **kwargs,
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
        **kwargs,
    ) -> "Message":
        """Send a video."""
        return await self.client.send_video(
            chat_id=self.chat.id,
            video=str(video) if isinstance(video, Path) else video,
            caption=caption,
            parse_mode=parse_mode,
            duration=duration,
            width=width,
            height=height,
            reply_to_message_id=self.message_id,
            thumb=thumb,
            has_spoiler=spoiler,
            **kwargs,
        )

    async def send_audio(
        self,
        audio: Union[str, Path, BinaryIO],
        caption: Optional[str] = None,
        duration: int = 0,
        performer: Optional[str] = None,
        title: Optional[str] = None,
        **kwargs,
    ) -> "Message":
        """Send an audio file."""
        return await self.client.send_audio(
            chat_id=self.chat.id,
            audio=str(audio) if isinstance(audio, Path) else audio,
            caption=caption,
            duration=duration,
            performer=performer,
            title=title,
            reply_to_message_id=self.message_id,
            **kwargs,
        )

    async def send_voice(
        self,
        voice: Union[str, Path, BinaryIO],
        caption: Optional[str] = None,
        duration: int = 0,
        **kwargs,
    ) -> "Message":
        """Send a voice message."""
        return await self.client.send_voice(
            chat_id=self.chat.id,
            voice=str(voice) if isinstance(voice, Path) else voice,
            caption=caption,
            duration=duration,
            reply_to_message_id=self.message_id,
            **kwargs,
        )

    async def send_video_note(
        self,
        video_note: Union[str, Path, BinaryIO],
        duration: int = 0,
        length: int = 1,
        **kwargs,
    ) -> "Message":
        """Send a video note (round video)."""
        return await self.client.send_video_note(
            chat_id=self.chat.id,
            video_note=str(video_note) if isinstance(video_note, Path) else video_note,
            duration=duration,
            length=length,
            reply_to_message_id=self.message_id,
            **kwargs,
        )

    async def send_sticker(self, sticker: Union[str, BinaryIO], **kwargs) -> "Message":
        """Send a sticker."""
        return await self.client.send_sticker(
            chat_id=self.chat.id,
            sticker=sticker,
            reply_to_message_id=self.message_id,
            **kwargs,
        )

    async def send_animation(
        self,
        animation: Union[str, Path, BinaryIO],
        caption: Optional[str] = None,
        **kwargs,
    ) -> "Message":
        """Send a GIF/animation."""
        return await self.client.send_animation(
            chat_id=self.chat.id,
            animation=str(animation) if isinstance(animation, Path) else animation,
            caption=caption,
            reply_to_message_id=self.message_id,
            **kwargs,
        )

    async def send_media_group(self, media: List[Any], **kwargs) -> List["Message"]:
        """Send a media group (album)."""
        return await self.client.send_media_group(
            chat_id=self.chat.id,
            media=media,
            reply_to_message_id=self.message_id,
            **kwargs,
        )

    # ==========================================================================
    # MESSAGE OPERATIONS
    # ==========================================================================

    async def forward(
        self, chat_id: int, disable_notification: bool = False
    ) -> "Message":
        """Forward the message to another chat."""
        return await self.client.forward_messages(
            chat_id=chat_id,
            from_chat_id=self.chat.id,
            message_ids=[self.message_id],
            disable_notification=disable_notification,
        )

    async def copy(
        self, chat_id: int, caption: Optional[str] = None, **kwargs
    ) -> "Message":
        """Copy the message to another chat."""
        return await self.client.copy_message(
            chat_id=chat_id,
            from_chat_id=self.chat.id,
            message_id=self.message_id,
            caption=caption,
            **kwargs,
        )

    async def pin(
        self, disable_notification: bool = False, both_sides: bool = False
    ) -> bool:
        """Pin the message."""
        try:
            await self.client.pin_chat_message(
                chat_id=self.chat.id,
                message_id=self.message_id,
                disable_notification=disable_notification,
                only_for_self=not both_sides,
            )
            return True
        except Exception:
            return False

    async def unpin(self) -> bool:
        """Unpin the message."""
        try:
            await self.client.unpin_chat_message(
                chat_id=self.chat.id,
                message_id=self.message_id,
            )
            return True
        except Exception:
            return False

    async def react(self, emoji: str) -> bool:
        """Add reaction to the message."""
        try:
            await self.client.set_message_reaction(
                chat_id=self.chat.id,
                message_id=self.message_id,
                reaction=emoji,
            )
            return True
        except Exception:
            return False

    # ==========================================================================
    # REPLY MESSAGE
    # ==========================================================================

    async def get_reply_message(self) -> Optional["TelegramContext"]:
        """Get the message being replied to."""
        if not self.is_reply:
            return None
        try:
            msg = await self.client.get_messages(
                chat_id=self.chat.id,
                message_ids=[self.raw.reply_to_message_id],
            )
            if msg:
                return TelegramContext(self.client, msg[0], command="", args=[])
        except Exception:
            pass
        return None

    async def get_reply_or_self(self) -> "TelegramContext":
        """Get reply message or self if not replying."""
        reply = await self.get_reply_message()
        return reply or self

    # ==========================================================================
    # MEDIA DOWNLOAD
    # ==========================================================================

    async def download_media(
        self, path: Optional[str] = None, progress: Optional[callable] = None
    ) -> Optional[str]:
        """Download media from the message."""
        if not self.has_media:
            return None
        return await self.client.download_media(
            message=self.raw,
            file_name=path,
            progress=progress,
        )

    # ==========================================================================
    # CHAT ACTIONS
    # ==========================================================================

    async def typing(self):
        """Send 'typing' action."""
        await self.client.send_chat_action(self.chat.id, "typing")

    async def upload_photo(self):
        """Send 'uploading photo' action."""
        await self.client.send_chat_action(self.chat.id, "upload_photo")

    async def upload_video(self):
        """Send 'uploading video' action."""
        await self.client.send_chat_action(self.chat.id, "upload_video")

    async def upload_document(self):
        """Send 'uploading document' action."""
        await self.client.send_chat_action(self.chat.id, "upload_document")

    async def record_voice(self):
        """Send 'recording voice' action."""
        await self.client.send_chat_action(self.chat.id, "record_voice")

    async def record_video(self):
        """Send 'recording video' action."""
        await self.client.send_chat_action(self.chat.id, "record_video")

    async def cancel_action(self):
        """Cancel any chat action."""
        await self.client.send_chat_action(self.chat.id, "cancel")

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
            return member.status in ("administrator", "creator")
        except Exception:
            return False

    async def is_owner(self, user_id: Optional[int] = None) -> bool:
        """Check if user is owner of current chat."""
        if self.is_private:
            return True
        try:
            member = await self.get_chat_member(user_id)
            return member.status == "creator"
        except Exception:
            return False

    # ==========================================================================
    # MODERATION
    # ==========================================================================

    async def ban_user(self, user_id: Optional[int] = None, until_date: int = 0) -> bool:
        """Ban user from chat."""
        try:
            uid = user_id or self.user.id
            await self.client.ban_chat_member(
                chat_id=self.chat.id,
                user_id=uid,
                until_date=until_date,
            )
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
        self, user_id: Optional[int] = None, until_date: int = 0
    ) -> bool:
        """Mute user in chat."""
        try:
            uid = user_id or self.user.id
            await self.client.restrict_chat_member(
                chat_id=self.chat.id,
                user_id=uid,
                permissions={},  # Empty = no permissions = muted
                until_date=until_date,
            )
            return True
        except Exception:
            return False

    async def unmute_user(self, user_id: Optional[int] = None) -> bool:
        """Unmute user in chat."""
        try:
            uid = user_id or self.user.id
            await self.client.restrict_chat_member(
                chat_id=self.chat.id,
                user_id=uid,
                permissions={
                    "can_send_messages": True,
                    "can_send_media_messages": True,
                    "can_send_other_messages": True,
                    "can_add_web_page_previews": True,
                },
            )
            return True
        except Exception:
            return False

    # ==========================================================================
    # INLINE KEYBOARDS
    # ==========================================================================

    @staticmethod
    def button(text: str, callback_data: str = None, url: str = None) -> dict:
        """Create an inline button."""
        btn = {"text": text}
        if url:
            btn["url"] = url
        else:
            btn["callback_data"] = callback_data or text
        return btn

    @staticmethod
    def keyboard(*rows: List) -> dict:
        """Create an inline keyboard from rows of buttons."""
        return {"inline_keyboard": [list(row) for row in rows]}

    # ==========================================================================
    # CALLBACK QUERIES
    # ==========================================================================

    async def answer_callback(
        self,
        text: str = "",
        show_alert: bool = False,
        url: Optional[str] = None,
        cache_time: int = 0,
    ) -> bool:
        """Answer callback query (if this is a callback)."""
        callback_id = getattr(self.raw, "callback_query_id", None)
        if callback_id:
            try:
                await self.client.answer_callback_query(
                    callback_query_id=callback_id,
                    text=text,
                    show_alert=show_alert,
                    url=url,
                    cache_time=cache_time,
                )
                return True
            except Exception:
                pass
        return False
