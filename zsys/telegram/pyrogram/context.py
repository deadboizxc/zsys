"""PyrogramContext — full-featured Pyrogram message context adapter.

Wraps a raw ``pyrogram.types.Message`` and the associated ``pyrogram.Client``
into a unified ``Context`` interface (``zsys.core.dataclass_models.context``),
providing every Telegram operation — media, moderation, keyboards, chat actions,
reactions — through a clean, consistent async API.

Note:
    This module is part of the ``zsys.telegram.pyrogram`` subsystem.
    ``PyrogramContext`` is the object received by all ``@command``-decorated
    handlers registered via the zsys module system.  For advanced use-cases the
    raw Pyrogram message is always accessible as ``ctx.raw``.

Example::

    @command("ping")
    async def ping(ctx: PyrogramContext) -> None:
        await ctx.answer("pong")
"""
# RU: PyrogramContext — полнофункциональный адаптер контекста сообщения для Pyrogram.
# RU: Оборачивает pyrogram.types.Message и pyrogram.Client в единый интерфейс Context,
# RU: предоставляя все операции Telegram через чистый асинхронный API.

from __future__ import annotations

from typing import Any, Optional, Union, List, BinaryIO, TYPE_CHECKING
from pathlib import Path

from zsys.core.dataclass_models.context import Context, User, Chat

if TYPE_CHECKING:
    from pyrogram import Client
    from pyrogram.types import Message, InlineKeyboardMarkup, ReplyKeyboardMarkup


class PyrogramContext(Context):
    """Full-featured Pyrogram message context implementing the unified Context interface.

    Wraps ``pyrogram.types.Message`` and ``pyrogram.Client`` and exposes every
    Telegram capability — messaging, media, moderation, chat actions, keyboards,
    reactions — through a consistent async API compatible with the zsys module
    system.  Raw Pyrogram objects remain accessible for advanced usage.

    Attributes:
        platform: Always ``"pyrogram"``.
        client: The underlying ``pyrogram.Client`` instance.
        raw: The raw ``pyrogram.types.Message`` object.
        command: The command string that triggered this handler (may be empty).
        args: Tokenised argument list parsed from the command invocation.
        text: Full text or caption of the message.
        user: Lazily-built :class:`User` dataclass from the message sender.
        chat: Lazily-built :class:`Chat` dataclass from the message chat.
        message_id: Integer ID of the triggering message.
        is_reply: ``True`` if the message is a reply to another message.
        is_self: ``True`` if the message was sent by the userbot owner.
        has_media: ``True`` if the message contains any media.
        media_type: String name of the media type, or ``None``.

    Example::

        @command("example")
        async def example(ctx: PyrogramContext) -> None:
            await ctx.typing()
            reply_ctx = await ctx.get_reply_message()
            await ctx.answer(f"Replied to: {reply_ctx.text if reply_ctx else 'nothing'}")
    """
    # RU: Полнофункциональный контекст сообщения Pyrogram, реализующий интерфейс Context.
    # RU: Оборачивает pyrogram.types.Message и pyrogram.Client, предоставляя все операции
    # RU: Telegram через единый асинхронный API.
    
    platform: str = "pyrogram"
    
    def __init__(
        self,
        client: "Client",
        message: "Message",
        command: str = "",
        args: List[str] = None
    ):
        """Initialise the context from a live client and a raw Pyrogram message.

        Args:
            client: Active ``pyrogram.Client`` instance that received the message.
            message: Raw ``pyrogram.types.Message`` object being processed.
            command: Parsed command name; empty string when not a command trigger.
            args: Tokenised argument list; defaults to an empty list.
        """
        # RU: Инициализировать контекст из активного клиента и сырого сообщения Pyrogram.
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
        """Return lazily-built User dataclass from the message sender.

        Returns:
            :class:`User` populated from ``message.from_user``; a zero-id User
            is returned when no sender is present (e.g. channel posts).
        """
        # RU: Вернуть лениво построенный объект User из отправителя сообщения.
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
        """Return lazily-built Chat dataclass from the message chat.

        Returns:
            :class:`Chat` populated from ``message.chat`` with type, title,
            username, description, and members count where available.
        """
        # RU: Вернуть лениво построенный объект Chat из чата сообщения.
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
        """Return the integer ID of the triggering message.

        Returns:
            Message ID as provided by Telegram.
        """
        # RU: Вернуть целочисленный ID инициирующего сообщения.
        return self.raw.id
    
    @property
    def is_reply(self) -> bool:
        """Check whether this message is a reply to another message.

        Returns:
            ``True`` if ``reply_to_message`` is set on the raw message.
        """
        # RU: Проверить, является ли сообщение ответом на другое сообщение.
        return self.raw.reply_to_message is not None
    
    @property
    def is_self(self) -> bool:
        """Check whether the message was sent by the userbot owner.

        Returns:
            ``True`` if ``from_user.is_self`` is set on the raw message.
        """
        # RU: Проверить, отправлено ли сообщение владельцем userbot-а.
        return self.raw.from_user and self.raw.from_user.is_self
    
    @property
    def has_media(self) -> bool:
        """Check whether the message contains any media attachment.

        Returns:
            ``True`` if the ``media`` field of the raw message is not ``None``.
        """
        # RU: Проверить, содержит ли сообщение медиавложение.
        return self.raw.media is not None
    
    @property
    def media_type(self) -> Optional[str]:
        """Return the string name of the media type, or ``None`` if no media.

        Returns:
            Enum value string (e.g. ``"photo"``, ``"video"``) when media is
            present, or ``None`` for text-only messages.
        """
        # RU: Вернуть строковое имя типа медиа или None, если медиа отсутствует.
        if self.raw.media:
            return self.raw.media.value if hasattr(self.raw.media, 'value') else str(self.raw.media)
        return None
    
    # ==========================================================================
    # CORE METHODS
    # ==========================================================================
    
    def _parse_mode(self, mode: Optional[str]):
        """Convert a string parse-mode name to the corresponding Pyrogram enum value.

        Args:
            mode: One of ``"markdown"``, ``"html"``, or any other value (maps to
                ``ParseMode.DISABLED``).

        Returns:
            The matching ``pyrogram.enums.ParseMode`` enum member.
        """
        # RU: Преобразовать строковое название режима разбора в enum Pyrogram.
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
        """Send a reply to the current message.

        Args:
            text: Message text to send.
            parse_mode: Formatting mode — ``"markdown"``, ``"html"``, or ``None``
                to disable formatting.  Defaults to ``"markdown"``.
            disable_preview: Suppress web-page link previews.  Defaults to ``True``.
            reply_markup: Optional inline keyboard markup to attach.
            **kwargs: Extra keyword arguments forwarded to ``Message.reply``.

        Returns:
            The sent ``pyrogram.types.Message``.

        Example::

            sent = await ctx.reply("Hello, world!")
        """
        # RU: Отправить ответ на текущее сообщение.
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
        """Edit the current message in place.

        Args:
            text: New text to replace the message content.
            parse_mode: Formatting mode — ``"markdown"``, ``"html"``, or ``None``.
                Defaults to ``"markdown"``.
            disable_preview: Suppress web-page link previews.  Defaults to ``True``.
            reply_markup: Optional inline keyboard markup to attach.
            **kwargs: Extra keyword arguments forwarded to ``Message.edit_text``.

        Returns:
            The edited ``pyrogram.types.Message``.

        Raises:
            pyrogram.errors.MessageNotModified: If the new text matches the current text.

        Example::

            await ctx.edit("Updated content")
        """
        # RU: Отредактировать текущее сообщение на месте.
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
        """Delete the current message.

        Args:
            revoke: If ``True`` (default), delete for all participants; if ``False``,
                delete only for the current user.

        Returns:
            ``True`` on success, ``False`` if deletion failed (e.g. insufficient rights).

        Example::

            deleted = await ctx.delete()
        """
        # RU: Удалить текущее сообщение.
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
        """Smart-reply — edit if message is from the userbot, reply otherwise.

        Provides a single call that does the right thing depending on whether
        the handler is processing its own output (edit in-place) or an incoming
        message from another user (thread-reply).

        Args:
            text: Message text to send or replace.
            parse_mode: Formatting mode — ``"markdown"``, ``"html"``, or ``None``.
                Defaults to ``"markdown"``.
            **kwargs: Extra keyword arguments forwarded to :meth:`edit` or :meth:`reply`.

        Returns:
            The resulting ``pyrogram.types.Message``.

        Example::

            await ctx.answer("Done!")
        """
        # RU: Умный ответ — редактирует своё сообщение или отправляет reply на чужое.
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
        """Send a photo as a reply to the current message.

        Args:
            photo: File path, URL, ``file_id``, or binary stream of the photo.
            caption: Optional caption text.
            parse_mode: Caption formatting — ``"markdown"``, ``"html"``, or ``None``.
            reply_markup: Optional inline keyboard markup to attach.
            spoiler: If ``True``, hide the photo behind a spoiler overlay.
            **kwargs: Extra keyword arguments forwarded to ``Message.reply_photo``.

        Returns:
            The sent ``pyrogram.types.Message``.

        Example::

            await ctx.send_photo("image.jpg", caption="Look at this!")
        """
        # RU: Отправить фото как ответ на текущее сообщение.
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
        """Send a file/document as a reply to the current message.

        Args:
            document: File path, URL, ``file_id``, or binary stream.
            caption: Optional caption text.
            parse_mode: Caption formatting — ``"markdown"``, ``"html"``, or ``None``.
            thumb: Optional thumbnail file path or binary stream.
            **kwargs: Extra keyword arguments forwarded to ``Message.reply_document``.

        Returns:
            The sent ``pyrogram.types.Message``.

        Example::

            await ctx.send_document("report.pdf", caption="Monthly report")
        """
        # RU: Отправить файл/документ как ответ на текущее сообщение.
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
        """Send a video as a reply to the current message.

        Args:
            video: File path, URL, ``file_id``, or binary stream of the video.
            caption: Optional caption text.
            parse_mode: Caption formatting — ``"markdown"``, ``"html"``, or ``None``.
            duration: Video duration in seconds.
            width: Video width in pixels.
            height: Video height in pixels.
            thumb: Optional thumbnail file path or binary stream.
            spoiler: If ``True``, hide the video behind a spoiler overlay.
            **kwargs: Extra keyword arguments forwarded to ``Message.reply_video``.

        Returns:
            The sent ``pyrogram.types.Message``.

        Example::

            await ctx.send_video("clip.mp4", caption="Watch this", duration=30)
        """
        # RU: Отправить видео как ответ на текущее сообщение.
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
        """Send an audio file as a reply to the current message.

        Args:
            audio: File path, URL, ``file_id``, or binary stream of the audio.
            caption: Optional caption text.
            duration: Track duration in seconds.
            performer: Artist / performer name shown in the audio player.
            title: Track title shown in the audio player.
            **kwargs: Extra keyword arguments forwarded to ``Message.reply_audio``.

        Returns:
            The sent ``pyrogram.types.Message``.

        Example::

            await ctx.send_audio("song.mp3", performer="Artist", title="Track")
        """
        # RU: Отправить аудиофайл как ответ на текущее сообщение.
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
        """Send a voice message as a reply to the current message.

        Args:
            voice: File path, URL, ``file_id``, or binary stream (OGG/OPUS format).
            caption: Optional caption text.
            duration: Duration of the voice message in seconds.
            **kwargs: Extra keyword arguments forwarded to ``Message.reply_voice``.

        Returns:
            The sent ``pyrogram.types.Message``.

        Example::

            await ctx.send_voice("voice.ogg", duration=5)
        """
        # RU: Отправить голосовое сообщение как ответ на текущее сообщение.
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
        """Send a round video note as a reply to the current message.

        Args:
            video_note: File path, URL, ``file_id``, or binary stream of a
                square MP4 video (Telegram displays these as round bubbles).
            duration: Duration of the video note in seconds.
            length: Side length in pixels of the square video.
            **kwargs: Extra keyword arguments forwarded to ``Message.reply_video_note``.

        Returns:
            The sent ``pyrogram.types.Message``.

        Example::

            await ctx.send_video_note("circle.mp4", duration=10, length=240)
        """
        # RU: Отправить круглое видео-заметку как ответ на текущее сообщение.
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
        """Send a sticker as a reply to the current message.

        Args:
            sticker: ``file_id``, URL, file path, or binary stream of the sticker
                (WebP, TGS, or WEBM format).
            **kwargs: Extra keyword arguments forwarded to ``Message.reply_sticker``.

        Returns:
            The sent ``pyrogram.types.Message``.

        Example::

            await ctx.send_sticker("CAACAgI...")
        """
        # RU: Отправить стикер как ответ на текущее сообщение.
        return await self.raw.reply_sticker(sticker, **kwargs)
    
    async def send_animation(
        self,
        animation: Union[str, Path, BinaryIO],
        caption: Optional[str] = None,
        **kwargs
    ) -> "Message":
        """Send a GIF or animation as a reply to the current message.

        Args:
            animation: File path, URL, ``file_id``, or binary stream (GIF / MP4).
            caption: Optional caption text.
            **kwargs: Extra keyword arguments forwarded to ``Message.reply_animation``.

        Returns:
            The sent ``pyrogram.types.Message``.

        Example::

            await ctx.send_animation("funny.gif", caption="lol")
        """
        # RU: Отправить GIF или анимацию как ответ на текущее сообщение.
        return await self.raw.reply_animation(animation, caption=caption, **kwargs)
    
    async def send_media_group(
        self,
        media: List[Any],
        **kwargs
    ) -> List["Message"]:
        """Send a media group (album) as a reply to the current message.

        Args:
            media: List of ``InputMediaPhoto``, ``InputMediaVideo``, or other
                Pyrogram ``InputMedia*`` objects to send as a single album.
            **kwargs: Extra keyword arguments forwarded to ``Client.send_media_group``.

        Returns:
            List of sent ``pyrogram.types.Message`` objects (one per media item).

        Example::

            from pyrogram.types import InputMediaPhoto
            await ctx.send_media_group([
                InputMediaPhoto("a.jpg"),
                InputMediaPhoto("b.jpg"),
            ])
        """
        # RU: Отправить медиагруппу (альбом) как ответ на текущее сообщение.
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
        """Forward the current message to another chat.

        Args:
            chat_id: Target chat ID or username.
            disable_notification: If ``True``, forward silently without a notification.

        Returns:
            The forwarded ``pyrogram.types.Message`` in the target chat.

        Example::

            await ctx.forward(chat_id=-1001234567890)
        """
        # RU: Переслать текущее сообщение в другой чат.
        return await self.raw.forward(chat_id, disable_notification=disable_notification)
    
    async def copy(
        self,
        chat_id: int,
        caption: Optional[str] = None,
        **kwargs
    ) -> "Message":
        """Copy the current message to another chat without the forwarded-from tag.

        Args:
            chat_id: Target chat ID or username.
            caption: Override caption for media messages; ``None`` keeps original.
            **kwargs: Extra keyword arguments forwarded to ``Message.copy``.

        Returns:
            The new ``pyrogram.types.Message`` in the target chat.

        Example::

            await ctx.copy(chat_id=-1001234567890, caption="Copied!")
        """
        # RU: Скопировать текущее сообщение в другой чат без тега «переслано от».
        return await self.raw.copy(chat_id, caption=caption, **kwargs)
    
    async def pin(self, disable_notification: bool = False, both_sides: bool = False) -> bool:
        """Pin the current message in the chat.

        Args:
            disable_notification: If ``True``, pin silently without a notification.
            both_sides: If ``True``, pin for both sides of a private conversation.

        Returns:
            ``True`` on success, ``False`` if pinning failed (e.g. insufficient rights).

        Example::

            pinned = await ctx.pin(disable_notification=True)
        """
        # RU: Закрепить текущее сообщение в чате.
        try:
            await self.raw.pin(disable_notification=disable_notification, both_sides=both_sides)
            return True
        except Exception:
            return False
    
    async def unpin(self) -> bool:
        """Unpin the current message in the chat.

        Returns:
            ``True`` on success, ``False`` if unpinning failed.

        Example::

            await ctx.unpin()
        """
        # RU: Открепить текущее сообщение в чате.
        try:
            await self.raw.unpin()
            return True
        except Exception:
            return False
    
    async def react(self, emoji: str) -> bool:
        """Add an emoji reaction to the current message.

        Args:
            emoji: Unicode emoji string to react with (e.g. ``"👍"``).

        Returns:
            ``True`` on success, ``False`` if the reaction could not be applied.

        Example::

            await ctx.react("🔥")
        """
        # RU: Добавить эмодзи-реакцию на текущее сообщение.
        try:
            await self.raw.react(emoji)
            return True
        except Exception:
            return False
    
    # ==========================================================================
    # REPLY MESSAGE
    # ==========================================================================
    
    async def get_reply_message(self) -> Optional["PyrogramContext"]:
        """Retrieve the message that the current message is replying to.

        Returns:
            A new :class:`PyrogramContext` wrapping the replied-to message, or
            ``None`` if the current message is not a reply.

        Example::

            reply_ctx = await ctx.get_reply_message()
            if reply_ctx:
                await ctx.answer(f"Replying to: {reply_ctx.text}")
        """
        # RU: Получить сообщение, на которое отвечает текущее сообщение.
        if self.raw.reply_to_message:
            return PyrogramContext(
                self.client,
                self.raw.reply_to_message,
                command="",
                args=[]
            )
        return None
    
    async def get_reply_or_self(self) -> "PyrogramContext":
        """Return the replied-to context, falling back to self if not a reply.

        Returns:
            The :class:`PyrogramContext` of the replied-to message when available,
            or the current context otherwise.

        Example::

            target = await ctx.get_reply_or_self()
            await ctx.answer(f"Target text: {target.text}")
        """
        # RU: Вернуть контекст ответа или себя, если не является ответом.
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
        """Download the media attached to the current message to disk.

        Args:
            path: Destination file path.  When ``None``, Pyrogram chooses the path
                automatically (usually ``./downloads/<filename>``).
            progress: Optional async progress callback ``(current, total)`` called
                periodically during download.

        Returns:
            Absolute path to the downloaded file, or ``None`` if the message has
            no media.

        Example::

            file_path = await ctx.download_media(path="/tmp/my_file")
        """
        # RU: Скачать медиа из текущего сообщения на диск.
        if not self.raw.media:
            return None
        return await self.raw.download(file_name=path, progress=progress)
    
    # ==========================================================================
    # CHAT ACTIONS
    # ==========================================================================
    
    async def typing(self):
        """Send the ``TYPING`` chat action to indicate the bot is composing a message.

        Example::

            await ctx.typing()
            result = expensive_computation()
            await ctx.answer(result)
        """
        # RU: Отправить действие «печатает» в текущий чат.
        from pyrogram.enums import ChatAction
        await self.client.send_chat_action(self.chat.id, ChatAction.TYPING)
    
    async def upload_photo(self):
        """Send the ``UPLOAD_PHOTO`` chat action to indicate a photo is being uploaded.

        Example::

            await ctx.upload_photo()
        """
        # RU: Отправить действие «загружает фото» в текущий чат.
        from pyrogram.enums import ChatAction
        await self.client.send_chat_action(self.chat.id, ChatAction.UPLOAD_PHOTO)
    
    async def upload_video(self):
        """Send the ``UPLOAD_VIDEO`` chat action to indicate a video is being uploaded.

        Example::

            await ctx.upload_video()
        """
        # RU: Отправить действие «загружает видео» в текущий чат.
        from pyrogram.enums import ChatAction
        await self.client.send_chat_action(self.chat.id, ChatAction.UPLOAD_VIDEO)
    
    async def upload_document(self):
        """Send the ``UPLOAD_DOCUMENT`` chat action to indicate a file is being uploaded.

        Example::

            await ctx.upload_document()
        """
        # RU: Отправить действие «загружает документ» в текущий чат.
        from pyrogram.enums import ChatAction
        await self.client.send_chat_action(self.chat.id, ChatAction.UPLOAD_DOCUMENT)
    
    async def record_voice(self):
        """Send the ``RECORD_VOICE`` chat action to indicate a voice message is being recorded.

        Example::

            await ctx.record_voice()
        """
        # RU: Отправить действие «записывает голосовое» в текущий чат.
        from pyrogram.enums import ChatAction
        await self.client.send_chat_action(self.chat.id, ChatAction.RECORD_VOICE)
    
    async def record_video(self):
        """Send the ``RECORD_VIDEO`` chat action to indicate a video note is being recorded.

        Example::

            await ctx.record_video()
        """
        # RU: Отправить действие «записывает видео» в текущий чат.
        from pyrogram.enums import ChatAction
        await self.client.send_chat_action(self.chat.id, ChatAction.RECORD_VIDEO)
    
    async def cancel_action(self):
        """Cancel any active chat action, removing the typing/uploading indicator.

        Example::

            await ctx.cancel_action()
        """
        # RU: Отменить любое активное действие в чате (убрать индикатор).
        from pyrogram.enums import ChatAction
        await self.client.send_chat_action(self.chat.id, ChatAction.CANCEL)
    
    # ==========================================================================
    # USER/CHAT INFO
    # ==========================================================================
    
    async def get_user_info(self, user_id: Optional[int] = None) -> Any:
        """Fetch full Pyrogram user object for a given user.

        Args:
            user_id: Telegram user ID to look up.  Defaults to the message sender.

        Returns:
            ``pyrogram.types.User`` with all available profile information.

        Example::

            user = await ctx.get_user_info()
            await ctx.answer(f"Name: {user.first_name}")
        """
        # RU: Получить полный объект пользователя Pyrogram по ID.
        uid = user_id or self.user.id
        return await self.client.get_users(uid)
    
    async def get_chat_info(self, chat_id: Optional[int] = None) -> Any:
        """Fetch full Pyrogram chat object for a given chat.

        Args:
            chat_id: Telegram chat ID or username to look up.  Defaults to
                the current message chat.

        Returns:
            ``pyrogram.types.Chat`` with all available chat metadata.

        Example::

            chat = await ctx.get_chat_info()
            await ctx.answer(f"Chat: {chat.title}")
        """
        # RU: Получить полный объект чата Pyrogram по ID.
        cid = chat_id or self.chat.id
        return await self.client.get_chat(cid)
    
    async def get_chat_member(self, user_id: Optional[int] = None) -> Any:
        """Fetch chat member info for a user in the current chat.

        Args:
            user_id: Telegram user ID to look up.  Defaults to the message sender.

        Returns:
            ``pyrogram.types.ChatMember`` with status and permissions.

        Raises:
            pyrogram.errors.UserNotParticipant: If the user is not in the chat.

        Example::

            member = await ctx.get_chat_member()
            await ctx.answer(f"Status: {member.status}")
        """
        # RU: Получить информацию об участнике текущего чата по ID.
        uid = user_id or self.user.id
        return await self.client.get_chat_member(self.chat.id, uid)
    
    async def is_admin(self, user_id: Optional[int] = None) -> bool:
        """Check whether a user has administrator or owner status in the current chat.

        Args:
            user_id: Telegram user ID to check.  Defaults to the message sender.

        Returns:
            ``True`` if the user is an admin or owner, or if the chat is private.
            ``False`` on error or if the user is a regular member.

        Example::

            if await ctx.is_admin():
                await ctx.answer("You are an admin!")
        """
        # RU: Проверить, является ли пользователь администратором или владельцем чата.
        if self.is_private:
            return True
        try:
            member = await self.get_chat_member(user_id)
            from pyrogram.enums import ChatMemberStatus
            return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)
        except Exception:
            return False
    
    async def is_owner(self, user_id: Optional[int] = None) -> bool:
        """Check whether a user is the owner of the current chat.

        Args:
            user_id: Telegram user ID to check.  Defaults to the message sender.

        Returns:
            ``True`` if the user is the chat owner, or if the chat is private.
            ``False`` on error or if the user is not the owner.

        Example::

            if await ctx.is_owner():
                await ctx.answer("You own this chat!")
        """
        # RU: Проверить, является ли пользователь владельцем текущего чата.
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
        """Permanently ban a user from the current chat.

        Args:
            user_id: Telegram user ID to ban.  Defaults to the message sender.

        Returns:
            ``True`` on success, ``False`` if banning failed (e.g. insufficient rights).

        Example::

            banned = await ctx.ban_user(user_id=123456789)
        """
        # RU: Навсегда забанить пользователя в текущем чате.
        try:
            uid = user_id or self.user.id
            await self.client.ban_chat_member(self.chat.id, uid)
            return True
        except Exception:
            return False
    
    async def unban_user(self, user_id: Optional[int] = None) -> bool:
        """Unban a previously banned user, allowing them to rejoin the chat.

        Args:
            user_id: Telegram user ID to unban.  Defaults to the message sender.

        Returns:
            ``True`` on success, ``False`` if unbanning failed.

        Example::

            await ctx.unban_user(user_id=123456789)
        """
        # RU: Разбанить пользователя в текущем чате.
        try:
            uid = user_id or self.user.id
            await self.client.unban_chat_member(self.chat.id, uid)
            return True
        except Exception:
            return False
    
    async def kick_user(self, user_id: Optional[int] = None) -> bool:
        """Kick a user from the chat by banning then immediately unbanning them.

        Args:
            user_id: Telegram user ID to kick.  Defaults to the message sender.

        Returns:
            ``True`` if both ban and unban succeeded, ``False`` otherwise.

        Example::

            kicked = await ctx.kick_user(user_id=123456789)
        """
        # RU: Выгнать пользователя из чата (бан + разбан).
        uid = user_id or self.user.id
        if await self.ban_user(uid):
            return await self.unban_user(uid)
        return False
    
    async def mute_user(
        self,
        user_id: Optional[int] = None,
        until_date: int = 0
    ) -> bool:
        """Restrict a user so they cannot send messages in the current chat.

        Args:
            user_id: Telegram user ID to mute.  Defaults to the message sender.
            until_date: Unix timestamp until which the restriction lasts.  Pass
                ``0`` (default) for a permanent mute.

        Returns:
            ``True`` on success, ``False`` if restriction failed.

        Example::

            import time
            await ctx.mute_user(user_id=123456789, until_date=int(time.time()) + 3600)
        """
        # RU: Ограничить пользователя в правах на отправку сообщений в чате.
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
        """Restore full message permissions for a muted user in the current chat.

        Args:
            user_id: Telegram user ID to unmute.  Defaults to the message sender.

        Returns:
            ``True`` on success, ``False`` if the operation failed.

        Example::

            await ctx.unmute_user(user_id=123456789)
        """
        # RU: Восстановить права на отправку сообщений для пользователя в чате.
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
        """Create a single inline keyboard button.

        Args:
            text: Label text displayed on the button.
            callback_data: Callback data string sent to the bot when pressed.
                Defaults to the button text when neither ``callback_data`` nor
                ``url`` are provided.
            url: URL to open when the button is pressed.  Takes precedence over
                ``callback_data`` when both are provided.

        Returns:
            ``pyrogram.types.InlineKeyboardButton`` instance.

        Example::

            btn = PyrogramContext.button("Click me", callback_data="action:do")
        """
        # RU: Создать одну кнопку встроенной клавиатуры.
        from pyrogram.types import InlineKeyboardButton
        if url:
            return InlineKeyboardButton(text, url=url)
        return InlineKeyboardButton(text, callback_data=callback_data or text)
    
    @staticmethod
    def keyboard(*rows: List):
        """Build an inline keyboard markup from rows of buttons.

        Args:
            *rows: Variable number of iterables, each containing
                ``InlineKeyboardButton`` objects that form one row.

        Returns:
            ``pyrogram.types.InlineKeyboardMarkup`` ready to attach to a message.

        Example::

            kb = PyrogramContext.keyboard(
                [PyrogramContext.button("Yes", "yes"), PyrogramContext.button("No", "no")],
            )
            await ctx.reply("Choose:", reply_markup=kb)
        """
        # RU: Собрать разметку встроенной клавиатуры из строк кнопок.
        from pyrogram.types import InlineKeyboardMarkup
        return InlineKeyboardMarkup([list(row) for row in rows])
    
    # ==========================================================================
    # INLINE QUERIES (for callback handling)
    # ==========================================================================
    
    async def answer_callback(self, text: str = "", show_alert: bool = False) -> bool:
        """Answer a callback query attached to the current context, if applicable.

        Args:
            text: Notification text to show to the user (up to 200 characters).
                Empty string (default) shows no notification.
            show_alert: If ``True``, show an alert dialog instead of a toast.

        Returns:
            ``True`` if the callback was answered, ``False`` if the raw object has
            no ``answer`` method (i.e. this is not a callback query context).

        Example::

            await ctx.answer_callback("Processing…", show_alert=False)
        """
        # RU: Ответить на callback-запрос, если текущий контекст является callback-запросом.
        if hasattr(self.raw, 'answer'):
            try:
                await self.raw.answer(text, show_alert=show_alert)
                return True
            except Exception:
                pass
        return False
