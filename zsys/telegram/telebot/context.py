"""
pyTelegramBotAPI (telebot) context adapter.

Wraps sync telebot in async interface for unified module system.
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Optional, Union, List, BinaryIO, TYPE_CHECKING
from pathlib import Path

from zsys.core.dataclass_models.context import Context, User, Chat

if TYPE_CHECKING:
    from telebot import TeleBot
    from telebot.types import Message, InlineKeyboardMarkup, ReplyKeyboardMarkup


# Thread pool for running sync telebot methods
_executor = ThreadPoolExecutor(max_workers=4)


async def _run_sync(func, *args, **kwargs):
    """Run sync function in thread pool."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, lambda: func(*args, **kwargs))


class TelebotContext(Context):
    """pyTelegramBotAPI (telebot) context implementing the unified interface.

    Wraps a synchronous ``TeleBot`` instance and a ``telebot.types.Message``
    object, executing every API call in a thread pool via ``_run_sync`` to
    expose a fully async API compatible with the zsys ``Context`` base class.

    Attributes:
        platform: Always ``"telebot"``.
        client: The synchronous ``TeleBot`` instance (same as ``bot``).
        bot: Alias for ``client``; the synchronous ``TeleBot`` instance.
        raw: Underlying ``telebot.types.Message`` object.
        command: Parsed command name (without prefix), or empty string.
        args: Whitespace-split arguments following the command.
        text: Message text or caption; empty string if absent.

    Example::

        ctx = TelebotContext(bot, message, command="start")
        await ctx.reply("Hello!")
    """
    # RU: Контекст telebot — реализует унифицированный Context через пул потоков.
    
    platform: str = "telebot"
    
    def __init__(
        self,
        bot: "TeleBot",
        message: "Message",
        command: str = "",
        args: List[str] = None
    ):
        """Initialise the context from a telebot bot instance and message.

        Args:
            bot: Synchronous ``TeleBot`` instance.
            message: Incoming ``telebot.types.Message`` object.
            command: Parsed command name (without leading ``/``). Defaults to ``""``.
            args: List of arguments following the command. Defaults to ``[]``.
        """
        # RU: Инициализация контекста из объектов TeleBot и Message.
        self.client = bot
        self.bot = bot  # Alias
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
        """Return the sender as a unified ``User`` dataclass.

        Lazily constructs the ``User`` from ``raw.from_user`` on first access.
        Returns a zeroed-out ``User(id=0)`` if the sender is absent.

        Returns:
            ``User`` dataclass populated from the telebot ``from_user`` field.

        Example::

            print(ctx.user.username)
        """
        # RU: Возвращает отправителя в виде унифицированного объекта User.
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
                    language_code=getattr(u, 'language_code', None),
                    is_premium=getattr(u, 'is_premium', False),
                )
        return self._user
    
    @property
    def chat(self) -> Chat:
        """Return the chat as a unified ``Chat`` dataclass.

        Lazily constructs the ``Chat`` from ``raw.chat`` on first access.

        Returns:
            ``Chat`` dataclass populated from the telebot ``chat`` field.

        Example::

            print(ctx.chat.id)
        """
        # RU: Возвращает чат в виде унифицированного объекта Chat.
        if self._chat is None:
            c = self.raw.chat
            self._chat = Chat(
                id=c.id,
                type=c.type,
                title=getattr(c, 'title', None),
                username=getattr(c, 'username', None),
            )
        return self._chat
    
    @property
    def message_id(self) -> int:
        """Return the integer ID of the incoming message.

        Returns:
            Message ID from ``raw.message_id``.

        Example::

            print(ctx.message_id)
        """
        # RU: Возвращает целочисленный идентификатор входящего сообщения.
        return self.raw.message_id
    
    @property
    def is_reply(self) -> bool:
        """Indicate whether the incoming message is a reply to another message.

        Returns:
            ``True`` if ``raw.reply_to_message`` is set, ``False`` otherwise.

        Example::

            if ctx.is_reply:
                replied = await ctx.get_reply_message()
        """
        # RU: Возвращает True, если сообщение является ответом на другое.
        return self.raw.reply_to_message is not None
    
    @property
    def has_media(self) -> bool:
        """Indicate whether the message contains any media attachment.

        Checks for photo, video, document, audio, voice, sticker, animation,
        and video note.

        Returns:
            ``True`` if at least one media type is present.

        Example::

            if ctx.has_media:
                await ctx.download_media()
        """
        # RU: Возвращает True, если сообщение содержит медиавложение.
        return bool(
            self.raw.photo or self.raw.video or self.raw.document or
            self.raw.audio or self.raw.voice or self.raw.sticker or
            getattr(self.raw, 'animation', None) or
            getattr(self.raw, 'video_note', None)
        )
    
    # ==========================================================================
    # CORE METHODS
    # ==========================================================================
    
    def _parse_mode(self, mode: Optional[str]) -> Optional[str]:
        """Convert parse mode to telebot format."""
        if mode == "markdown":
            return "Markdown"
        elif mode == "html":
            return "HTML"
        return None
    
    async def reply(
        self,
        text: str,
        parse_mode: Optional[str] = "markdown",
        disable_preview: bool = True,
        reply_markup: Optional["InlineKeyboardMarkup"] = None,
        **kwargs
    ) -> "Message":
        """Reply to the message."""
        return await _run_sync(
            self.bot.reply_to,
            self.raw,
            text,
            parse_mode=self._parse_mode(parse_mode),
            disable_web_page_preview=disable_preview,
            reply_markup=reply_markup
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
        return await _run_sync(
            self.bot.edit_message_text,
            text,
            self.chat.id,
            self.message_id,
            parse_mode=self._parse_mode(parse_mode),
            disable_web_page_preview=disable_preview,
            reply_markup=reply_markup
        )
    
    async def delete(self) -> bool:
        """Delete the message."""
        try:
            await _run_sync(self.bot.delete_message, self.chat.id, self.message_id)
            return True
        except Exception:
            return False
    
    async def answer(
        self,
        text: str,
        parse_mode: Optional[str] = "markdown",
        **kwargs
    ) -> "Message":
        """Bot always replies."""
        return await self.reply(text, parse_mode=parse_mode, **kwargs)
    
    async def send(
        self,
        text: str,
        parse_mode: Optional[str] = "markdown",
        reply_markup: Optional["InlineKeyboardMarkup"] = None,
        **kwargs
    ) -> "Message":
        """Send a new message (not reply)."""
        return await _run_sync(
            self.bot.send_message,
            self.chat.id,
            text,
            parse_mode=self._parse_mode(parse_mode),
            reply_markup=reply_markup
        )
    
    # ==========================================================================
    # MEDIA METHODS
    # ==========================================================================
    
    def _open_file(self, file: Union[str, Path, BinaryIO]) -> BinaryIO:
        """Open file if path provided."""
        if isinstance(file, (str, Path)):
            return open(file, 'rb')
        return file
    
    async def send_photo(
        self,
        photo: Union[str, Path, BinaryIO],
        caption: Optional[str] = None,
        parse_mode: Optional[str] = "markdown",
        reply_markup: Optional["InlineKeyboardMarkup"] = None,
        **kwargs
    ) -> "Message":
        """Send a photo."""
        return await _run_sync(
            self.bot.send_photo,
            self.chat.id,
            self._open_file(photo),
            caption=caption,
            parse_mode=self._parse_mode(parse_mode),
            reply_to_message_id=self.message_id,
            reply_markup=reply_markup
        )
    
    async def send_document(
        self,
        document: Union[str, Path, BinaryIO],
        caption: Optional[str] = None,
        parse_mode: Optional[str] = "markdown",
        **kwargs
    ) -> "Message":
        """Send a document."""
        return await _run_sync(
            self.bot.send_document,
            self.chat.id,
            self._open_file(document),
            caption=caption,
            parse_mode=self._parse_mode(parse_mode),
            reply_to_message_id=self.message_id
        )
    
    async def send_video(
        self,
        video: Union[str, Path, BinaryIO],
        caption: Optional[str] = None,
        parse_mode: Optional[str] = "markdown",
        duration: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        **kwargs
    ) -> "Message":
        """Send a video."""
        return await _run_sync(
            self.bot.send_video,
            self.chat.id,
            self._open_file(video),
            caption=caption,
            parse_mode=self._parse_mode(parse_mode),
            duration=duration,
            width=width,
            height=height,
            reply_to_message_id=self.message_id
        )
    
    async def send_audio(
        self,
        audio: Union[str, Path, BinaryIO],
        caption: Optional[str] = None,
        duration: Optional[int] = None,
        performer: Optional[str] = None,
        title: Optional[str] = None,
        **kwargs
    ) -> "Message":
        """Send an audio file."""
        return await _run_sync(
            self.bot.send_audio,
            self.chat.id,
            self._open_file(audio),
            caption=caption,
            duration=duration,
            performer=performer,
            title=title,
            reply_to_message_id=self.message_id
        )
    
    async def send_voice(
        self,
        voice: Union[str, Path, BinaryIO],
        caption: Optional[str] = None,
        duration: Optional[int] = None,
        **kwargs
    ) -> "Message":
        """Send a voice message."""
        return await _run_sync(
            self.bot.send_voice,
            self.chat.id,
            self._open_file(voice),
            caption=caption,
            duration=duration,
            reply_to_message_id=self.message_id
        )
    
    async def send_video_note(
        self,
        video_note: Union[str, Path, BinaryIO],
        duration: Optional[int] = None,
        length: Optional[int] = None,
        **kwargs
    ) -> "Message":
        """Send a video note (round video)."""
        return await _run_sync(
            self.bot.send_video_note,
            self.chat.id,
            self._open_file(video_note),
            duration=duration,
            length=length,
            reply_to_message_id=self.message_id
        )
    
    async def send_sticker(
        self,
        sticker: Union[str, BinaryIO],
        **kwargs
    ) -> "Message":
        """Send a sticker."""
        return await _run_sync(
            self.bot.send_sticker,
            self.chat.id,
            sticker if isinstance(sticker, str) else self._open_file(sticker),
            reply_to_message_id=self.message_id
        )
    
    async def send_animation(
        self,
        animation: Union[str, Path, BinaryIO],
        caption: Optional[str] = None,
        **kwargs
    ) -> "Message":
        """Send a GIF/animation."""
        return await _run_sync(
            self.bot.send_animation,
            self.chat.id,
            self._open_file(animation),
            caption=caption,
            reply_to_message_id=self.message_id
        )
    
    # ==========================================================================
    # MESSAGE OPERATIONS
    # ==========================================================================
    
    async def forward(self, chat_id: int, disable_notification: bool = False) -> "Message":
        """Forward the message to another chat."""
        return await _run_sync(
            self.bot.forward_message,
            chat_id,
            self.chat.id,
            self.message_id,
            disable_notification=disable_notification
        )
    
    async def copy(
        self,
        chat_id: int,
        caption: Optional[str] = None,
        **kwargs
    ) -> Any:
        """Copy the message to another chat."""
        return await _run_sync(
            self.bot.copy_message,
            chat_id,
            self.chat.id,
            self.message_id,
            caption=caption
        )
    
    async def pin(self, disable_notification: bool = False) -> bool:
        """Pin the message."""
        try:
            await _run_sync(
                self.bot.pin_chat_message,
                self.chat.id,
                self.message_id,
                disable_notification=disable_notification
            )
            return True
        except Exception:
            return False
    
    async def unpin(self) -> bool:
        """Unpin the message."""
        try:
            await _run_sync(
                self.bot.unpin_chat_message,
                self.chat.id,
                self.message_id
            )
            return True
        except Exception:
            return False
    
    # ==========================================================================
    # REPLY MESSAGE
    # ==========================================================================
    
    async def get_reply_message(self) -> Optional["TelebotContext"]:
        """Get the message being replied to."""
        if self.raw.reply_to_message:
            return TelebotContext(
                self.bot,
                self.raw.reply_to_message,
                command="",
                args=[]
            )
        return None
    
    # ==========================================================================
    # MEDIA DOWNLOAD
    # ==========================================================================
    
    async def download_media(self, path: Optional[str] = None) -> Optional[str]:
        """Download media from the message."""
        file_id = None
        
        if self.raw.photo:
            file_id = self.raw.photo[-1].file_id
        elif self.raw.video:
            file_id = self.raw.video.file_id
        elif self.raw.document:
            file_id = self.raw.document.file_id
        elif self.raw.audio:
            file_id = self.raw.audio.file_id
        elif self.raw.voice:
            file_id = self.raw.voice.file_id
        elif self.raw.sticker:
            file_id = self.raw.sticker.file_id
        
        if not file_id:
            return None
        
        file_info = await _run_sync(self.bot.get_file, file_id)
        downloaded = await _run_sync(self.bot.download_file, file_info.file_path)
        
        destination = path or f"downloads/{file_id}"
        Path(destination).parent.mkdir(parents=True, exist_ok=True)
        
        with open(destination, 'wb') as f:
            f.write(downloaded)
        
        return destination
    
    # ==========================================================================
    # CHAT ACTIONS
    # ==========================================================================
    
    async def typing(self):
        """Send 'typing' action."""
        await _run_sync(self.bot.send_chat_action, self.chat.id, "typing")
    
    async def upload_photo(self):
        """Send 'uploading photo' action."""
        await _run_sync(self.bot.send_chat_action, self.chat.id, "upload_photo")
    
    async def upload_video(self):
        """Send 'uploading video' action."""
        await _run_sync(self.bot.send_chat_action, self.chat.id, "upload_video")
    
    async def upload_document(self):
        """Send 'uploading document' action."""
        await _run_sync(self.bot.send_chat_action, self.chat.id, "upload_document")
    
    async def record_voice(self):
        """Send 'recording voice' action."""
        await _run_sync(self.bot.send_chat_action, self.chat.id, "record_voice")
    
    async def record_video(self):
        """Send 'recording video' action."""
        await _run_sync(self.bot.send_chat_action, self.chat.id, "record_video")
    
    # ==========================================================================
    # USER/CHAT INFO
    # ==========================================================================
    
    async def get_chat_member(self, user_id: Optional[int] = None) -> Any:
        """Get chat member info."""
        uid = user_id or self.user.id
        return await _run_sync(self.bot.get_chat_member, self.chat.id, uid)
    
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
            await _run_sync(
                self.bot.ban_chat_member,
                self.chat.id,
                uid,
                until_date=until_date or None
            )
            return True
        except Exception:
            return False
    
    async def unban_user(self, user_id: Optional[int] = None) -> bool:
        """Unban user from chat."""
        try:
            uid = user_id or self.user.id
            await _run_sync(self.bot.unban_chat_member, self.chat.id, uid)
            return True
        except Exception:
            return False
    
    async def kick_user(self, user_id: Optional[int] = None) -> bool:
        """Kick user from chat."""
        uid = user_id or self.user.id
        if await self.ban_user(uid):
            return await self.unban_user(uid)
        return False
    
    # ==========================================================================
    # INLINE KEYBOARDS
    # ==========================================================================
    
    @staticmethod
    def button(text: str, callback_data: str = None, url: str = None):
        """Create an inline button."""
        from telebot.types import InlineKeyboardButton
        if url:
            return InlineKeyboardButton(text, url=url)
        return InlineKeyboardButton(text, callback_data=callback_data or text)
    
    @staticmethod
    def keyboard(*rows: List):
        """Create an inline keyboard from rows of buttons."""
        from telebot.types import InlineKeyboardMarkup
        markup = InlineKeyboardMarkup()
        for row in rows:
            markup.add(*row)
        return markup
    
    # ==========================================================================
    # CALLBACK QUERIES
    # ==========================================================================
    
    async def answer_callback(
        self,
        text: str = "",
        show_alert: bool = False,
        url: Optional[str] = None,
        cache_time: int = 0
    ) -> bool:
        """Answer callback query."""
        if hasattr(self.raw, 'id'):
            try:
                await _run_sync(
                    self.bot.answer_callback_query,
                    self.raw.id,
                    text=text,
                    show_alert=show_alert,
                    url=url,
                    cache_time=cache_time
                )
                return True
            except Exception:
                pass
        return False
