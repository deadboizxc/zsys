"""
aiogram 3.x context adapter with full feature support.

Supports all aiogram features:
- Message operations
- Inline keyboards
- Callback query handling
- FSM states
- Throttling
- And more!
"""

from __future__ import annotations

from typing import Any, Optional, Union, List, BinaryIO, TYPE_CHECKING
from pathlib import Path

from zsys.core.dataclass_models.context import Context, User, Chat

if TYPE_CHECKING:
    from aiogram import Bot
    from aiogram.types import (
        Message,
        InlineKeyboardMarkup,
        ReplyKeyboardMarkup,
        FSInputFile,
    )
    from aiogram.fsm.context import FSMContext


class AiogramContext(Context):
    """
    Full-featured aiogram 3.x context.
    
    Provides all aiogram capabilities through the unified interface,
    plus direct access to raw aiogram objects for advanced usage.
    
    Usage:
        @command("example")
        async def example(ctx: AiogramContext):
            # Unified API
            await ctx.reply("Hello!")
            
            # aiogram-specific
            await ctx.answer_callback("Done!")  # For callbacks
            
            # Use FSM states
            await ctx.set_state(MyStates.waiting)
            
            # Direct access
            ctx.raw  # aiogram Message object
            ctx.bot  # aiogram Bot instance
    """
    
    platform: str = "aiogram"
    
    def __init__(
        self,
        message: "Message",
        bot: "Bot",
        command: str = "",
        args: List[str] = None,
        state: "FSMContext" = None
    ):
        self.raw = message
        self.client = bot
        self.bot = bot  # Alias for convenience
        self.command = command
        self.args = args or []
        self.text = message.text or message.caption or ""
        self.state = state
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
            self._chat = Chat(
                id=c.id,
                type=c.type,
                title=c.title,
                username=c.username,
            )
        return self._chat
    
    @property
    def message_id(self) -> int:
        return self.raw.message_id
    
    @property
    def is_reply(self) -> bool:
        return self.raw.reply_to_message is not None
    
    @property
    def has_media(self) -> bool:
        """Check if message has any media."""
        return bool(
            self.raw.photo or self.raw.video or self.raw.document or
            self.raw.audio or self.raw.voice or self.raw.sticker or
            self.raw.animation or self.raw.video_note
        )
    
    @property
    def media_type(self) -> Optional[str]:
        """Get media type if present."""
        if self.raw.photo:
            return "photo"
        elif self.raw.video:
            return "video"
        elif self.raw.document:
            return "document"
        elif self.raw.audio:
            return "audio"
        elif self.raw.voice:
            return "voice"
        elif self.raw.sticker:
            return "sticker"
        elif self.raw.animation:
            return "animation"
        elif self.raw.video_note:
            return "video_note"
        return None
    
    # ==========================================================================
    # CORE METHODS
    # ==========================================================================
    
    def _parse_mode(self, mode: Optional[str]) -> Optional[str]:
        """Convert parse mode to aiogram format."""
        if mode == "markdown":
            return "MarkdownV2"
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
        # Escape special chars for MarkdownV2
        if parse_mode == "markdown":
            # Use HTML instead to avoid escaping issues
            parse_mode = "html"
        
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
        if parse_mode == "markdown":
            parse_mode = "html"
        
        return await self.raw.edit_text(
            text,
            parse_mode=self._parse_mode(parse_mode),
            disable_web_page_preview=disable_preview,
            reply_markup=reply_markup,
            **kwargs
        )
    
    async def delete(self) -> bool:
        """Delete the message."""
        try:
            await self.raw.delete()
            return True
        except Exception:
            return False
    
    async def answer(
        self,
        text: str,
        parse_mode: Optional[str] = "markdown",
        **kwargs
    ) -> "Message":
        """Bot always replies (doesn't edit)."""
        return await self.reply(text, parse_mode=parse_mode, **kwargs)
    
    async def send(
        self,
        text: str,
        parse_mode: Optional[str] = "markdown",
        reply_markup: Optional["InlineKeyboardMarkup"] = None,
        **kwargs
    ) -> "Message":
        """Send a new message (not reply)."""
        if parse_mode == "markdown":
            parse_mode = "html"
        
        return await self.bot.send_message(
            self.chat.id,
            text,
            parse_mode=self._parse_mode(parse_mode),
            reply_markup=reply_markup,
            **kwargs
        )
    
    # ==========================================================================
    # MEDIA METHODS
    # ==========================================================================
    
    def _prepare_file(self, file: Union[str, Path, BinaryIO]):
        """Prepare file for sending."""
        from aiogram.types import FSInputFile
        if isinstance(file, (str, Path)) and Path(file).exists():
            return FSInputFile(file)
        return file
    
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
        if parse_mode == "markdown":
            parse_mode = "html"
        
        return await self.raw.reply_photo(
            self._prepare_file(photo),
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
        **kwargs
    ) -> "Message":
        """Send a document."""
        if parse_mode == "markdown":
            parse_mode = "html"
        
        return await self.raw.reply_document(
            self._prepare_file(document),
            caption=caption,
            parse_mode=self._parse_mode(parse_mode),
            **kwargs
        )
    
    async def send_video(
        self,
        video: Union[str, Path, BinaryIO],
        caption: Optional[str] = None,
        parse_mode: Optional[str] = "markdown",
        duration: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        spoiler: bool = False,
        **kwargs
    ) -> "Message":
        """Send a video."""
        if parse_mode == "markdown":
            parse_mode = "html"
        
        return await self.raw.reply_video(
            self._prepare_file(video),
            caption=caption,
            parse_mode=self._parse_mode(parse_mode),
            duration=duration,
            width=width,
            height=height,
            has_spoiler=spoiler,
            **kwargs
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
        return await self.raw.reply_audio(
            self._prepare_file(audio),
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
        duration: Optional[int] = None,
        **kwargs
    ) -> "Message":
        """Send a voice message."""
        return await self.raw.reply_voice(
            self._prepare_file(voice),
            caption=caption,
            duration=duration,
            **kwargs
        )
    
    async def send_video_note(
        self,
        video_note: Union[str, Path, BinaryIO],
        duration: Optional[int] = None,
        length: Optional[int] = None,
        **kwargs
    ) -> "Message":
        """Send a video note (round video)."""
        return await self.raw.reply_video_note(
            self._prepare_file(video_note),
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
        return await self.raw.reply_sticker(
            self._prepare_file(sticker) if isinstance(sticker, (str, Path)) else sticker,
            **kwargs
        )
    
    async def send_animation(
        self,
        animation: Union[str, Path, BinaryIO],
        caption: Optional[str] = None,
        **kwargs
    ) -> "Message":
        """Send a GIF/animation."""
        return await self.raw.reply_animation(
            self._prepare_file(animation),
            caption=caption,
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
    ) -> Any:
        """Copy the message to another chat."""
        return await self.raw.copy_to(chat_id, caption=caption, **kwargs)
    
    async def pin(self, disable_notification: bool = False) -> bool:
        """Pin the message."""
        try:
            await self.raw.pin(disable_notification=disable_notification)
            return True
        except Exception:
            return False
    
    async def unpin(self) -> bool:
        """Unpin the message."""
        try:
            await self.bot.unpin_chat_message(self.chat.id, self.message_id)
            return True
        except Exception:
            return False
    
    async def react(self, emoji: str) -> bool:
        """Add reaction to the message."""
        try:
            from aiogram.types import ReactionTypeEmoji
            await self.bot.set_message_reaction(
                self.chat.id,
                self.message_id,
                [ReactionTypeEmoji(emoji=emoji)]
            )
            return True
        except Exception:
            return False
    
    # ==========================================================================
    # REPLY MESSAGE
    # ==========================================================================
    
    async def get_reply_message(self) -> Optional["AiogramContext"]:
        """Get the message being replied to."""
        if self.raw.reply_to_message:
            return AiogramContext(
                self.raw.reply_to_message,
                self.bot,
                command="",
                args=[],
                state=self.state
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
        elif self.raw.animation:
            file_id = self.raw.animation.file_id
        elif self.raw.video_note:
            file_id = self.raw.video_note.file_id
        
        if not file_id:
            return None
        
        file = await self.bot.get_file(file_id)
        destination = path or f"downloads/{file_id}"
        await self.bot.download_file(file.file_path, destination)
        return destination
    
    # ==========================================================================
    # CHAT ACTIONS
    # ==========================================================================
    
    async def typing(self):
        """Send 'typing' action."""
        await self.bot.send_chat_action(self.chat.id, "typing")
    
    async def upload_photo(self):
        """Send 'uploading photo' action."""
        await self.bot.send_chat_action(self.chat.id, "upload_photo")
    
    async def upload_video(self):
        """Send 'uploading video' action."""
        await self.bot.send_chat_action(self.chat.id, "upload_video")
    
    async def upload_document(self):
        """Send 'uploading document' action."""
        await self.bot.send_chat_action(self.chat.id, "upload_document")
    
    async def record_voice(self):
        """Send 'recording voice' action."""
        await self.bot.send_chat_action(self.chat.id, "record_voice")
    
    async def record_video(self):
        """Send 'recording video' action."""
        await self.bot.send_chat_action(self.chat.id, "record_video")
    
    # ==========================================================================
    # USER/CHAT INFO
    # ==========================================================================
    
    async def get_chat_member(self, user_id: Optional[int] = None) -> Any:
        """Get chat member info."""
        uid = user_id or self.user.id
        return await self.bot.get_chat_member(self.chat.id, uid)
    
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
            await self.bot.ban_chat_member(self.chat.id, uid, until_date=until_date or None)
            return True
        except Exception:
            return False
    
    async def unban_user(self, user_id: Optional[int] = None) -> bool:
        """Unban a previously banned user from the current chat.

        Args:
            user_id: ID of the user to unban. Defaults to the sender's ID.

        Returns:
            ``True`` on success, ``False`` if the unban failed.

        Example::

            await ctx.unban_user(user_id=123456)
        """
        # RU: Снимает бан с пользователя в текущем чате.
        try:
            uid = user_id or self.user.id
            await self.bot.unban_chat_member(self.chat.id, uid)
            return True
        except Exception:
            return False
    
    async def kick_user(self, user_id: Optional[int] = None) -> bool:
        """Kick a user by banning and immediately unbanning them.

        Args:
            user_id: ID of the user to kick. Defaults to the sender's ID.

        Returns:
            ``True`` on success, ``False`` if the kick failed.

        Example::

            await ctx.kick_user(user_id=123456)
        """
        # RU: Выгоняет пользователя из чата (бан + разбан).
        uid = user_id or self.user.id
        if await self.ban_user(uid):
            return await self.unban_user(uid)
        return False
    
    # ==========================================================================
    # FSM STATES
    # ==========================================================================
    
    async def get_state(self) -> Optional[str]:
        """Return the current FSM state key as a string.

        Returns:
            Current state string, or ``None`` if no FSM context is set or
            the state is unset.

        Example::

            state = await ctx.get_state()
        """
        # RU: Возвращает текущее состояние FSM в виде строки.
        if self.state:
            return await self.state.get_state()
        return None
    
    async def set_state(self, state: Any = None):
        """Set the FSM state.

        Args:
            state: New state value (usually a ``State`` object or ``None`` to
                clear).

        Example::

            await ctx.set_state(MyStates.waiting)
        """
        # RU: Устанавливает состояние FSM.
        if self.state:
            await self.state.set_state(state)
    
    async def clear_state(self):
        """Clear the current FSM state and all associated data.

        Example::

            await ctx.clear_state()
        """
        # RU: Сбрасывает состояние FSM и связанные данные.
        if self.state:
            await self.state.clear()
    
    async def get_data(self) -> dict:
        """Return the FSM context data dictionary.

        Returns:
            Dictionary of key-value pairs stored in the FSM context, or an
            empty dict if no FSM context is set.

        Example::

            data = await ctx.get_data()
            print(data.get("username"))
        """
        # RU: Возвращает словарь данных FSM-контекста.
        if self.state:
            return await self.state.get_data()
        return {}
    
    async def set_data(self, **data):
        """Replace the FSM context data with the provided key-value pairs.

        Args:
            **data: Key-value pairs to store in the FSM context.

        Example::

            await ctx.set_data(step=1, username="alex")
        """
        # RU: Заменяет данные FSM-контекста переданными значениями.
        if self.state:
            await self.state.set_data(data)
    
    async def update_data(self, **data):
        """Merge new key-value pairs into the existing FSM context data.

        Args:
            **data: Key-value pairs to update in the FSM context.

        Example::

            await ctx.update_data(step=2)
        """
        # RU: Обновляет данные FSM-контекста, сохраняя существующие ключи.
        if self.state:
            await self.state.update_data(**data)
    
    # ==========================================================================
    # INLINE KEYBOARDS
    # ==========================================================================
    
    @staticmethod
    def button(text: str, callback_data: str = None, url: str = None):
        """Create an inline button."""
        from aiogram.types import InlineKeyboardButton
        if url:
            return InlineKeyboardButton(text=text, url=url)
        return InlineKeyboardButton(text=text, callback_data=callback_data or text)
    
    @staticmethod
    def keyboard(*rows: List):
        """Create an inline keyboard from rows of buttons."""
        from aiogram.types import InlineKeyboardMarkup
        return InlineKeyboardMarkup(inline_keyboard=[list(row) for row in rows])
    
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
        """Answer callback query (if this is a callback context)."""
        # This is typically called from CallbackQuery handler
        if hasattr(self.raw, 'answer'):
            try:
                await self.raw.answer(
                    text=text,
                    show_alert=show_alert,
                    url=url,
                    cache_time=cache_time
                )
                return True
            except Exception:
                pass
        return False
