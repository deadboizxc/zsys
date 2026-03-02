"""pyTelegramBotAPI context adapter — async wrapper for synchronous telebot.

Wraps every synchronous ``TeleBot`` API call in ``asyncio``'s thread-pool
executor via ``_run_sync``, providing a fully async ``TelebotContext`` that
implements the zsys ``Context`` interface.

Note:
    Requires the ``telebot`` extra: ``pip install zsys[telegram-telebot]``.

Example::

    from zsys.telegram.telebot import TelebotContext

    async def handler(ctx: TelebotContext):
        await ctx.reply("Hello from telebot!")
"""
# RU: Контекстный адаптер pyTelegramBotAPI — асинхронная обёртка над синхронным telebot.
# RU: Все вызовы API выполняются в пуле потоков через _run_sync.

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
    """Execute a synchronous callable in the shared thread-pool executor.

    Wraps ``loop.run_in_executor`` so that blocking telebot API calls do not
    stall the asyncio event loop.

    Args:
        func: Synchronous callable to run.
        *args: Positional arguments forwarded to ``func``.
        **kwargs: Keyword arguments forwarded to ``func``.

    Returns:
        Awaitable that resolves to the return value of ``func``.
    """
    # RU: Запускает синхронную функцию в пуле потоков, не блокируя event loop.
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
        """Convert a unified parse-mode string to the telebot format.

        Args:
            mode: ``"markdown"`` returns ``"Markdown"``, ``"html"`` returns
                ``"HTML"``, any other value returns ``None``.

        Returns:
            telebot-compatible parse mode string, or ``None``.
        """
        # RU: Преобразует строку режима разметки в формат telebot.
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
        """Reply to the incoming message with text.

        Executes ``bot.reply_to`` in the thread pool.

        Args:
            text: Reply text.
            parse_mode: Markup mode — ``"markdown"``, ``"html"``, or ``None``.
                Defaults to ``"markdown"``.
            disable_preview: Disable web-page preview. Defaults to ``True``.
            reply_markup: Optional inline keyboard markup.
            **kwargs: Ignored (kept for interface compatibility).

        Returns:
            Sent ``telebot.types.Message`` object.

        Example::

            await ctx.reply("Hello!")
        """
        # RU: Отправляет ответ на входящее сообщение через пул потоков.
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
        """Edit the text of the current message in-place.

        Args:
            text: New message text.
            parse_mode: Markup mode. Defaults to ``"markdown"``.
            disable_preview: Disable web-page preview. Defaults to ``True``.
            reply_markup: Optional updated inline keyboard markup.
            **kwargs: Ignored (kept for interface compatibility).

        Returns:
            Updated ``telebot.types.Message`` object.

        Example::

            await ctx.edit("Updated text")
        """
        # RU: Редактирует текст текущего сообщения.
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
        """Delete the current message.

        Returns:
            ``True`` on success, ``False`` if deletion failed.

        Example::

            deleted = await ctx.delete()
        """
        # RU: Удаляет текущее сообщение; возвращает False при ошибке.
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
        """Send a reply to the message (alias for :meth:`reply`).

        Args:
            text: Answer text.
            parse_mode: Markup mode. Defaults to ``"markdown"``.
            **kwargs: Extra keyword arguments forwarded to :meth:`reply`.

        Returns:
            Sent ``telebot.types.Message`` object.

        Example::

            await ctx.answer("Got it!")
        """
        # RU: Отправляет ответное сообщение (псевдоним reply).
        return await self.reply(text, parse_mode=parse_mode, **kwargs)
    
    async def send(
        self,
        text: str,
        parse_mode: Optional[str] = "markdown",
        reply_markup: Optional["InlineKeyboardMarkup"] = None,
        **kwargs
    ) -> "Message":
        """Send a new independent message to the current chat (not a reply).

        Args:
            text: Message text.
            parse_mode: Markup mode. Defaults to ``"markdown"``.
            reply_markup: Optional inline keyboard markup.
            **kwargs: Ignored (kept for interface compatibility).

        Returns:
            Sent ``telebot.types.Message`` object.

        Example::

            await ctx.send("Broadcast message")
        """
        # RU: Отправляет новое сообщение в текущий чат (не ответ).
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
        """Open a local file path for binary reading; pass through streams.

        Args:
            file: File path (``str`` or ``Path``) or an already-open binary
                stream.

        Returns:
            Open binary file object, or the original stream if it was already
            a binary IO object.
        """
        # RU: Открывает файл по пути; пропускает уже открытые потоки без изменений.
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
        """Send a photo as a reply to the current message.

        Args:
            photo: File path, ``Path``, binary stream, or Telegram ``file_id``.
            caption: Optional caption text.
            parse_mode: Caption markup mode. Defaults to ``"markdown"``.
            reply_markup: Optional inline keyboard markup.
            **kwargs: Ignored (kept for interface compatibility).

        Returns:
            Sent ``telebot.types.Message`` object.

        Example::

            await ctx.send_photo("image.jpg", caption="Look!")
        """
        # RU: Отправляет фото в ответ на текущее сообщение.
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
        """Send a document as a reply to the current message.

        Args:
            document: File path, ``Path``, binary stream, or Telegram ``file_id``.
            caption: Optional caption text.
            parse_mode: Caption markup mode. Defaults to ``"markdown"``.
            **kwargs: Ignored (kept for interface compatibility).

        Returns:
            Sent ``telebot.types.Message`` object.

        Example::

            await ctx.send_document("report.pdf", caption="Report")
        """
        # RU: Отправляет документ в ответ на текущее сообщение.
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
        """Send a video as a reply to the current message.

        Args:
            video: File path, ``Path``, binary stream, or Telegram ``file_id``.
            caption: Optional caption text.
            parse_mode: Caption markup mode. Defaults to ``"markdown"``.
            duration: Video duration in seconds.
            width: Video width in pixels.
            height: Video height in pixels.
            **kwargs: Ignored (kept for interface compatibility).

        Returns:
            Sent ``telebot.types.Message`` object.

        Example::

            await ctx.send_video("clip.mp4")
        """
        # RU: Отправляет видео в ответ на текущее сообщение.
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
        """Send an audio file as a reply to the current message.

        Args:
            audio: File path, ``Path``, binary stream, or Telegram ``file_id``.
            caption: Optional caption text.
            duration: Audio duration in seconds.
            performer: Performer name shown in the audio player.
            title: Track title shown in the audio player.
            **kwargs: Ignored (kept for interface compatibility).

        Returns:
            Sent ``telebot.types.Message`` object.

        Example::

            await ctx.send_audio("song.mp3", title="My Song")
        """
        # RU: Отправляет аудиофайл в ответ на текущее сообщение.
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
        """Send a voice message as a reply to the current message.

        Args:
            voice: File path, ``Path``, binary stream, or Telegram ``file_id``.
            caption: Optional caption text.
            duration: Voice message duration in seconds.
            **kwargs: Ignored (kept for interface compatibility).

        Returns:
            Sent ``telebot.types.Message`` object.

        Example::

            await ctx.send_voice("note.ogg")
        """
        # RU: Отправляет голосовое сообщение в ответ на текущее.
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
        """Send a round video note as a reply to the current message.

        Args:
            video_note: File path, ``Path``, binary stream, or Telegram ``file_id``.
            duration: Video note duration in seconds.
            length: Video note side dimension in pixels (must be square).
            **kwargs: Ignored (kept for interface compatibility).

        Returns:
            Sent ``telebot.types.Message`` object.

        Example::

            await ctx.send_video_note("circle.mp4")
        """
        # RU: Отправляет круглое видео (video note) в ответ на текущее сообщение.
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
        """Send a sticker as a reply to the current message.

        Args:
            sticker: Telegram ``file_id`` string or binary stream.
            **kwargs: Ignored (kept for interface compatibility).

        Returns:
            Sent ``telebot.types.Message`` object.

        Example::

            await ctx.send_sticker("CAACAgIAAxkBAAI...")
        """
        # RU: Отправляет стикер в ответ на текущее сообщение.
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
        """Send a GIF or animation as a reply to the current message.

        Args:
            animation: File path, ``Path``, binary stream, or Telegram ``file_id``.
            caption: Optional caption text.
            **kwargs: Ignored (kept for interface compatibility).

        Returns:
            Sent ``telebot.types.Message`` object.

        Example::

            await ctx.send_animation("reaction.gif")
        """
        # RU: Отправляет GIF-анимацию в ответ на текущее сообщение.
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
        """Forward the current message to another chat.

        Args:
            chat_id: Target chat identifier.
            disable_notification: If ``True``, send silently. Defaults to ``False``.

        Returns:
            The forwarded ``telebot.types.Message`` object.

        Example::

            await ctx.forward(chat_id=-100123456789)
        """
        # RU: Пересылает текущее сообщение в другой чат.
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
        """Copy the current message to another chat without a forward header.

        Args:
            chat_id: Target chat identifier.
            caption: Optional new caption to replace the original one.
            **kwargs: Ignored (kept for interface compatibility).

        Returns:
            ``MessageId`` of the copy on success.

        Example::

            await ctx.copy(chat_id=-100123456789)
        """
        # RU: Копирует сообщение в другой чат без заголовка пересылки.
        return await _run_sync(
            self.bot.copy_message,
            chat_id,
            self.chat.id,
            self.message_id,
            caption=caption
        )
    
    async def pin(self, disable_notification: bool = False) -> bool:
        """Pin the current message in the chat.

        Args:
            disable_notification: If ``True``, pin silently. Defaults to ``False``.

        Returns:
            ``True`` on success, ``False`` if pinning failed.

        Example::

            await ctx.pin()
        """
        # RU: Закрепляет текущее сообщение в чате.
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
        """Unpin the current message in the chat.

        Returns:
            ``True`` on success, ``False`` if unpinning failed.

        Example::

            await ctx.unpin()
        """
        # RU: Открепляет текущее сообщение в чате.
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
        """Return the message being replied to, wrapped in a new context.

        Returns:
            A new ``TelebotContext`` wrapping ``raw.reply_to_message``, or
            ``None`` if the message is not a reply.

        Example::

            if ctx.is_reply:
                replied_ctx = await ctx.get_reply_message()
                print(replied_ctx.text)
        """
        # RU: Возвращает контекст сообщения, на которое отвечает текущее.
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
        """Download the media attachment of the current message to disk.

        Selects the best available ``file_id`` (largest photo size for photos)
        and downloads via ``bot.download_file``.

        Args:
            path: Destination file path. Defaults to ``"downloads/<file_id>"``.

        Returns:
            The destination path string on success, or ``None`` if the message
            has no downloadable media.

        Example::

            saved = await ctx.download_media("/tmp/photo.jpg")
        """
        # RU: Скачивает медиавложение сообщения на диск.
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
        """Send a ``typing`` chat action indicator to the current chat.

        Example::

            await ctx.typing()
        """
        # RU: Показывает индикатор «печатает…» в текущем чате.
        await _run_sync(self.bot.send_chat_action, self.chat.id, "typing")
    
    async def upload_photo(self):
        """Send an ``upload_photo`` chat action indicator to the current chat.

        Example::

            await ctx.upload_photo()
        """
        # RU: Показывает индикатор загрузки фото в текущем чате.
        await _run_sync(self.bot.send_chat_action, self.chat.id, "upload_photo")
    
    async def upload_video(self):
        """Send an ``upload_video`` chat action indicator to the current chat.

        Example::

            await ctx.upload_video()
        """
        # RU: Показывает индикатор загрузки видео в текущем чате.
        await _run_sync(self.bot.send_chat_action, self.chat.id, "upload_video")
    
    async def upload_document(self):
        """Send an ``upload_document`` chat action indicator to the current chat.

        Example::

            await ctx.upload_document()
        """
        # RU: Показывает индикатор загрузки документа в текущем чате.
        await _run_sync(self.bot.send_chat_action, self.chat.id, "upload_document")
    
    async def record_voice(self):
        """Send a ``record_voice`` chat action indicator to the current chat.

        Example::

            await ctx.record_voice()
        """
        # RU: Показывает индикатор записи голосового сообщения в текущем чате.
        await _run_sync(self.bot.send_chat_action, self.chat.id, "record_voice")
    
    async def record_video(self):
        """Send a ``record_video`` chat action indicator to the current chat.

        Example::

            await ctx.record_video()
        """
        # RU: Показывает индикатор записи видео в текущем чате.
        await _run_sync(self.bot.send_chat_action, self.chat.id, "record_video")
    
    # ==========================================================================
    # USER/CHAT INFO
    # ==========================================================================
    
    async def get_chat_member(self, user_id: Optional[int] = None) -> Any:
        """Fetch chat-member status for a user in the current chat.

        Args:
            user_id: Target user ID. Defaults to the sender's ID.

        Returns:
            ``telebot.types.ChatMember`` object with status and permissions.

        Example::

            member = await ctx.get_chat_member()
        """
        # RU: Получает информацию об участнике текущего чата.
        uid = user_id or self.user.id
        return await _run_sync(self.bot.get_chat_member, self.chat.id, uid)
    
    async def is_admin(self, user_id: Optional[int] = None) -> bool:
        """Check whether a user holds admin privileges in the current chat.

        Always returns ``True`` in private chats.

        Args:
            user_id: Target user ID. Defaults to the sender's ID.

        Returns:
            ``True`` if the user is ``administrator`` or ``creator``.

        Example::

            if await ctx.is_admin():
                await ctx.reply("Welcome, admin!")
        """
        # RU: Проверяет, является ли пользователь администратором в текущем чате.
        if self.is_private:
            return True
        try:
            member = await self.get_chat_member(user_id)
            return member.status in ("administrator", "creator")
        except Exception:
            return False
    
    async def is_owner(self, user_id: Optional[int] = None) -> bool:
        """Check whether a user is the owner (creator) of the current chat.

        Always returns ``True`` in private chats.

        Args:
            user_id: Target user ID. Defaults to the sender's ID.

        Returns:
            ``True`` if the user's status is ``"creator"``.

        Example::

            if await ctx.is_owner():
                await ctx.reply("Welcome, owner!")
        """
        # RU: Проверяет, является ли пользователь владельцем текущего чата.
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
        """Ban a user from the current chat.

        Args:
            user_id: ID of the user to ban. Defaults to the sender's ID.
            until_date: Unix timestamp of the ban expiry. ``0`` means permanent.

        Returns:
            ``True`` on success, ``False`` if the ban failed.

        Example::

            await ctx.ban_user(user_id=123456)
        """
        # RU: Банит пользователя в текущем чате.
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
            await _run_sync(self.bot.unban_chat_member, self.chat.id, uid)
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
    # INLINE KEYBOARDS
    # ==========================================================================
    
    @staticmethod
    def button(text: str, callback_data: str = None, url: str = None):
        """Create a single ``InlineKeyboardButton``.

        Args:
            text: Button label shown to the user.
            callback_data: Callback data sent on press. Defaults to ``text``.
            url: URL to open on press (mutually exclusive with
                ``callback_data``).

        Returns:
            ``telebot.types.InlineKeyboardButton`` instance.

        Example::

            btn = TelebotContext.button("Click me", callback_data="btn_1")
        """
        # RU: Создаёт кнопку инлайн-клавиатуры telebot.
        from telebot.types import InlineKeyboardButton
        if url:
            return InlineKeyboardButton(text, url=url)
        return InlineKeyboardButton(text, callback_data=callback_data or text)
    
    @staticmethod
    def keyboard(*rows: List):
        """Build an ``InlineKeyboardMarkup`` from rows of buttons.

        Args:
            *rows: Each positional argument is an iterable of
                ``InlineKeyboardButton`` objects representing one row.

        Returns:
            ``telebot.types.InlineKeyboardMarkup`` ready to attach as
            ``reply_markup``.

        Example::

            kb = TelebotContext.keyboard(
                [TelebotContext.button("Yes", "yes"), TelebotContext.button("No", "no")]
            )
        """
        # RU: Собирает InlineKeyboardMarkup из строк кнопок telebot.
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
        """Answer a callback query originating from this context.

        Args:
            text: Optional notification text shown to the user.
            show_alert: If ``True``, show a blocking alert dialog.
            url: URL to open on the client side.
            cache_time: Seconds the client may cache the answer.

        Returns:
            ``True`` on success, ``False`` if the raw message has no ``id``
            attribute or if the call failed.

        Example::

            await ctx.answer_callback("Done!")
        """
        # RU: Отвечает на callback-запрос; снимает индикатор загрузки с кнопки.
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
