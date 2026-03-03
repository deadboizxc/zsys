"""Aiogram 3.x context adapter — full-featured unified message context.

Wraps an ``aiogram.types.Message`` together with the active ``Bot`` and
optional ``FSMContext`` into a single ``AiogramContext`` that implements the
zsys ``Context`` interface, covering messaging, media, moderation, FSM, and
inline keyboards.

Note:
    Intended for use inside aiogram handler functions or via
    ``zsys.telegram.aiogram.router.attach_router``.

Example::

    from zsys.telegram.aiogram import AiogramContext

    async def handler(message, bot, state):
        ctx = AiogramContext(message, bot, state=state)
        await ctx.reply("Hello!")
"""
# RU: Контекстный адаптер aiogram 3.x, реализующий унифицированный интерфейс Context.
# RU: Объединяет Message, Bot и FSMContext в единый объект для удобной работы с сообщениями.

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
    """Full-featured aiogram 3.x context implementing the unified interface.

    Wraps a raw ``aiogram.types.Message``, the active ``Bot`` instance, and an
    optional ``FSMContext`` to expose all Telegram capabilities — messaging,
    media, moderation, FSM, and inline keyboards — through a single consistent
    API.  Raw aiogram objects remain accessible for advanced use cases.

    Attributes:
        platform: Always ``"aiogram"``.
        raw: Underlying ``aiogram.types.Message`` object.
        client: Active ``aiogram.Bot`` instance (same object as ``bot``).
        bot: Alias for ``client``; the active ``aiogram.Bot`` instance.
        command: Parsed command name (without prefix), or empty string.
        args: Whitespace-split arguments following the command.
        text: Message text or caption; empty string if absent.
        state: Optional ``aiogram.fsm.context.FSMContext`` for state machines.

    Example::

        ctx = AiogramContext(message, bot, command="start", state=fsm_state)
        await ctx.reply("Hello!")
        await ctx.set_state(MyStates.waiting)
    """

    # RU: Полнофункциональный контекст aiogram 3.x на основе унифицированного Context.

    platform: str = "aiogram"

    def __init__(
        self,
        message: "Message",
        bot: "Bot",
        command: str = "",
        args: List[str] = None,
        state: "FSMContext" = None,
    ):
        """Initialise the context from an aiogram message, bot, and optional FSM state.

        Args:
            message: Incoming ``aiogram.types.Message`` object.
            bot: Active ``aiogram.Bot`` instance.
            command: Parsed command name (without leading ``/``). Defaults to ``""``.
            args: List of arguments following the command. Defaults to ``[]``.
            state: Optional ``FSMContext`` for finite-state machine operations.
        """
        # RU: Инициализация контекста из объектов aiogram Message, Bot и FSMContext.
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
        """Return the sender as a unified ``User`` dataclass.

        Lazily constructs the ``User`` from ``raw.from_user`` on first access.
        Returns a zeroed-out ``User(id=0)`` if the sender is absent.

        Returns:
            ``User`` dataclass populated from the aiogram ``from_user`` field.

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
                    language_code=u.language_code,
                    is_premium=getattr(u, "is_premium", False),
                )
        return self._user

    @property
    def chat(self) -> Chat:
        """Return the chat as a unified ``Chat`` dataclass.

        Lazily constructs the ``Chat`` from ``raw.chat`` on first access.

        Returns:
            ``Chat`` dataclass populated from the aiogram ``chat`` field.

        Example::

            print(ctx.chat.id)
        """
        # RU: Возвращает чат в виде унифицированного объекта Chat.
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
        # RU: Возвращает True, если сообщение является ответом на другое сообщение.
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
        # RU: Возвращает True, если сообщение содержит медиавложение любого типа.
        return bool(
            self.raw.photo
            or self.raw.video
            or self.raw.document
            or self.raw.audio
            or self.raw.voice
            or self.raw.sticker
            or self.raw.animation
            or self.raw.video_note
        )

    @property
    def media_type(self) -> Optional[str]:
        """Return the media type of the message as a string, or ``None``.

        Returns:
            One of ``"photo"``, ``"video"``, ``"document"``, ``"audio"``,
            ``"voice"``, ``"sticker"``, ``"animation"``, ``"video_note"``,
            or ``None`` if the message has no media.

        Example::

            mtype = ctx.media_type  # e.g. "photo"
        """
        # RU: Возвращает строковое обозначение типа медиа или None.
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
        """Convert a unified parse-mode string to the aiogram format.

        Args:
            mode: ``"markdown"`` → ``"MarkdownV2"``, ``"html"`` → ``"HTML"``,
                any other value → ``None``.

        Returns:
            aiogram-compatible parse mode string, or ``None``.
        """
        # RU: Преобразует строку режима разметки в формат aiogram.
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
        **kwargs,
    ) -> "Message":
        """Reply to the incoming message with text.

        Sends the reply using ``raw.reply()``. When ``parse_mode`` is
        ``"markdown"`` it is silently promoted to ``"html"`` to avoid
        MarkdownV2 escaping issues.

        Args:
            text: Reply text.
            parse_mode: Markup mode — ``"markdown"`` (promoted to HTML),
                ``"html"``, or ``None``. Defaults to ``"markdown"``.
            disable_preview: Disable web-page preview. Defaults to ``True``.
            reply_markup: Optional inline keyboard markup.
            **kwargs: Extra keyword arguments forwarded to ``Message.reply``.

        Returns:
            Sent ``aiogram.types.Message`` object.

        Example::

            await ctx.reply("Hello <b>world</b>!")
        """
        # RU: Отправляет ответ на входящее сообщение; markdown автоматически заменяется на HTML.
        # Escape special chars for MarkdownV2
        if parse_mode == "markdown":
            # Use HTML instead to avoid escaping issues
            parse_mode = "html"

        return await self.raw.reply(
            text,
            parse_mode=self._parse_mode(parse_mode),
            disable_web_page_preview=disable_preview,
            reply_markup=reply_markup,
            **kwargs,
        )

    async def edit(
        self,
        text: str,
        parse_mode: Optional[str] = "markdown",
        disable_preview: bool = True,
        reply_markup: Optional["InlineKeyboardMarkup"] = None,
        **kwargs,
    ) -> "Message":
        """Edit the text of the current message in-place.

        Args:
            text: New message text.
            parse_mode: Markup mode. Defaults to ``"markdown"`` (promoted to HTML).
            disable_preview: Disable web-page preview. Defaults to ``True``.
            reply_markup: Optional updated inline keyboard markup.
            **kwargs: Extra keyword arguments forwarded to ``Message.edit_text``.

        Returns:
            Updated ``aiogram.types.Message`` object.

        Example::

            await ctx.edit("Updated text")
        """
        # RU: Редактирует текст текущего сообщения.
        if parse_mode == "markdown":
            parse_mode = "html"

        return await self.raw.edit_text(
            text,
            parse_mode=self._parse_mode(parse_mode),
            disable_web_page_preview=disable_preview,
            reply_markup=reply_markup,
            **kwargs,
        )

    async def delete(self) -> bool:
        """Delete the current message.

        Returns:
            ``True`` on success, ``False`` if deletion failed (e.g. no
            permission or the message is too old).

        Example::

            deleted = await ctx.delete()
        """
        # RU: Удаляет текущее сообщение; возвращает False при ошибке.
        try:
            await self.raw.delete()
            return True
        except Exception:
            return False

    async def answer(
        self, text: str, parse_mode: Optional[str] = "markdown", **kwargs
    ) -> "Message":
        """Send a reply to the message (alias for :meth:`reply`).

        Always sends a new reply message rather than editing.

        Args:
            text: Answer text.
            parse_mode: Markup mode. Defaults to ``"markdown"``.
            **kwargs: Extra keyword arguments forwarded to :meth:`reply`.

        Returns:
            Sent ``aiogram.types.Message`` object.

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
        **kwargs,
    ) -> "Message":
        """Send a new independent message to the current chat (not a reply).

        Args:
            text: Message text.
            parse_mode: Markup mode. Defaults to ``"markdown"`` (promoted to HTML).
            reply_markup: Optional inline keyboard markup.
            **kwargs: Extra keyword arguments forwarded to ``Bot.send_message``.

        Returns:
            Sent ``aiogram.types.Message`` object.

        Example::

            await ctx.send("Broadcast message")
        """
        # RU: Отправляет новое самостоятельное сообщение в текущий чат.
        if parse_mode == "markdown":
            parse_mode = "html"

        return await self.bot.send_message(
            self.chat.id,
            text,
            parse_mode=self._parse_mode(parse_mode),
            reply_markup=reply_markup,
            **kwargs,
        )

    # ==========================================================================
    # MEDIA METHODS
    # ==========================================================================

    def _prepare_file(self, file: Union[str, Path, BinaryIO]):
        """Wrap a local file path in ``FSInputFile``; pass through other types.

        Args:
            file: File path (``str`` or ``Path``) or an already-open binary
                stream.

        Returns:
            ``aiogram.types.FSInputFile`` if ``file`` is an existing path,
            otherwise the original object unchanged.
        """
        # RU: Оборачивает путь к файлу в FSInputFile для отправки через aiogram.
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
        **kwargs,
    ) -> "Message":
        """Send a photo as a reply to the current message.

        Args:
            photo: File path, ``Path``, binary stream, or Telegram ``file_id``.
            caption: Optional caption text.
            parse_mode: Caption markup mode. Defaults to ``"markdown"`` (→ HTML).
            reply_markup: Optional inline keyboard markup.
            spoiler: Whether to hide the photo behind a spoiler overlay.
            **kwargs: Extra keyword arguments forwarded to ``Message.reply_photo``.

        Returns:
            Sent ``aiogram.types.Message`` object.

        Example::

            await ctx.send_photo("image.jpg", caption="Look!")
        """
        # RU: Отправляет фото в ответ на текущее сообщение.
        if parse_mode == "markdown":
            parse_mode = "html"

        return await self.raw.reply_photo(
            self._prepare_file(photo),
            caption=caption,
            parse_mode=self._parse_mode(parse_mode),
            reply_markup=reply_markup,
            has_spoiler=spoiler,
            **kwargs,
        )

    async def send_document(
        self,
        document: Union[str, Path, BinaryIO],
        caption: Optional[str] = None,
        parse_mode: Optional[str] = "markdown",
        **kwargs,
    ) -> "Message":
        """Send a document as a reply to the current message.

        Args:
            document: File path, ``Path``, binary stream, or Telegram ``file_id``.
            caption: Optional caption text.
            parse_mode: Caption markup mode. Defaults to ``"markdown"`` (→ HTML).
            **kwargs: Extra keyword arguments forwarded to ``Message.reply_document``.

        Returns:
            Sent ``aiogram.types.Message`` object.

        Example::

            await ctx.send_document("report.pdf", caption="Here is the report.")
        """
        # RU: Отправляет документ в ответ на текущее сообщение.
        if parse_mode == "markdown":
            parse_mode = "html"

        return await self.raw.reply_document(
            self._prepare_file(document),
            caption=caption,
            parse_mode=self._parse_mode(parse_mode),
            **kwargs,
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
        **kwargs,
    ) -> "Message":
        """Send a video as a reply to the current message.

        Args:
            video: File path, ``Path``, binary stream, or Telegram ``file_id``.
            caption: Optional caption text.
            parse_mode: Caption markup mode. Defaults to ``"markdown"`` (→ HTML).
            duration: Video duration in seconds.
            width: Video width in pixels.
            height: Video height in pixels.
            spoiler: Whether to hide the video behind a spoiler overlay.
            **kwargs: Extra keyword arguments forwarded to ``Message.reply_video``.

        Returns:
            Sent ``aiogram.types.Message`` object.

        Example::

            await ctx.send_video("clip.mp4", caption="Watch this!")
        """
        # RU: Отправляет видео в ответ на текущее сообщение.
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
            **kwargs,
        )

    async def send_audio(
        self,
        audio: Union[str, Path, BinaryIO],
        caption: Optional[str] = None,
        duration: Optional[int] = None,
        performer: Optional[str] = None,
        title: Optional[str] = None,
        **kwargs,
    ) -> "Message":
        """Send an audio file as a reply to the current message.

        Args:
            audio: File path, ``Path``, binary stream, or Telegram ``file_id``.
            caption: Optional caption text.
            duration: Audio duration in seconds.
            performer: Performer name shown in the audio player.
            title: Track title shown in the audio player.
            **kwargs: Extra keyword arguments forwarded to ``Message.reply_audio``.

        Returns:
            Sent ``aiogram.types.Message`` object.

        Example::

            await ctx.send_audio("song.mp3", title="My Song")
        """
        # RU: Отправляет аудиофайл в ответ на текущее сообщение.
        return await self.raw.reply_audio(
            self._prepare_file(audio),
            caption=caption,
            duration=duration,
            performer=performer,
            title=title,
            **kwargs,
        )

    async def send_voice(
        self,
        voice: Union[str, Path, BinaryIO],
        caption: Optional[str] = None,
        duration: Optional[int] = None,
        **kwargs,
    ) -> "Message":
        """Send a voice message as a reply to the current message.

        Args:
            voice: File path, ``Path``, binary stream, or Telegram ``file_id``.
            caption: Optional caption text.
            duration: Voice message duration in seconds.
            **kwargs: Extra keyword arguments forwarded to ``Message.reply_voice``.

        Returns:
            Sent ``aiogram.types.Message`` object.

        Example::

            await ctx.send_voice("note.ogg")
        """
        # RU: Отправляет голосовое сообщение в ответ на текущее.
        return await self.raw.reply_voice(
            self._prepare_file(voice), caption=caption, duration=duration, **kwargs
        )

    async def send_video_note(
        self,
        video_note: Union[str, Path, BinaryIO],
        duration: Optional[int] = None,
        length: Optional[int] = None,
        **kwargs,
    ) -> "Message":
        """Send a round video note as a reply to the current message.

        Args:
            video_note: File path, ``Path``, binary stream, or Telegram ``file_id``.
            duration: Video note duration in seconds.
            length: Video note side dimension in pixels (must be square).
            **kwargs: Extra keyword arguments forwarded to ``Message.reply_video_note``.

        Returns:
            Sent ``aiogram.types.Message`` object.

        Example::

            await ctx.send_video_note("circle.mp4")
        """
        # RU: Отправляет круглое видео (video note) в ответ на текущее сообщение.
        return await self.raw.reply_video_note(
            self._prepare_file(video_note), duration=duration, length=length, **kwargs
        )

    async def send_sticker(self, sticker: Union[str, BinaryIO], **kwargs) -> "Message":
        """Send a sticker as a reply to the current message.

        Args:
            sticker: File path, binary stream, or Telegram ``file_id`` / URL.
            **kwargs: Extra keyword arguments forwarded to ``Message.reply_sticker``.

        Returns:
            Sent ``aiogram.types.Message`` object.

        Example::

            await ctx.send_sticker("CAACAgIAAxkBAAI...")
        """
        # RU: Отправляет стикер в ответ на текущее сообщение.
        return await self.raw.reply_sticker(
            self._prepare_file(sticker)
            if isinstance(sticker, (str, Path))
            else sticker,
            **kwargs,
        )

    async def send_animation(
        self,
        animation: Union[str, Path, BinaryIO],
        caption: Optional[str] = None,
        **kwargs,
    ) -> "Message":
        """Send a GIF or animation as a reply to the current message.

        Args:
            animation: File path, ``Path``, binary stream, or Telegram ``file_id``.
            caption: Optional caption text.
            **kwargs: Extra keyword arguments forwarded to ``Message.reply_animation``.

        Returns:
            Sent ``aiogram.types.Message`` object.

        Example::

            await ctx.send_animation("reaction.gif")
        """
        # RU: Отправляет GIF-анимацию в ответ на текущее сообщение.
        return await self.raw.reply_animation(
            self._prepare_file(animation), caption=caption, **kwargs
        )

    # ==========================================================================
    # MESSAGE OPERATIONS
    # ==========================================================================

    async def forward(
        self, chat_id: int, disable_notification: bool = False
    ) -> "Message":
        """Forward the current message to another chat.

        Args:
            chat_id: Target chat identifier.
            disable_notification: If ``True``, send silently. Defaults to ``False``.

        Returns:
            The forwarded ``aiogram.types.Message`` object.

        Example::

            await ctx.forward(chat_id=-100123456789)
        """
        # RU: Пересылает текущее сообщение в другой чат.
        return await self.raw.forward(
            chat_id, disable_notification=disable_notification
        )

    async def copy(self, chat_id: int, caption: Optional[str] = None, **kwargs) -> Any:
        """Copy the current message to another chat without a forward header.

        Args:
            chat_id: Target chat identifier.
            caption: Optional new caption to replace the original one.
            **kwargs: Extra keyword arguments forwarded to ``Message.copy_to``.

        Returns:
            ``MessageId`` of the copy on success.

        Example::

            await ctx.copy(chat_id=-100123456789)
        """
        # RU: Копирует сообщение в другой чат без заголовка пересылки.
        return await self.raw.copy_to(chat_id, caption=caption, **kwargs)

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
            await self.raw.pin(disable_notification=disable_notification)
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
            await self.bot.unpin_chat_message(self.chat.id, self.message_id)
            return True
        except Exception:
            return False

    async def react(self, emoji: str) -> bool:
        """Add an emoji reaction to the current message.

        Args:
            emoji: Unicode emoji string to react with (e.g. ``"👍"``).

        Returns:
            ``True`` on success, ``False`` if the reaction could not be set.

        Example::

            await ctx.react("👍")
        """
        # RU: Устанавливает эмодзи-реакцию на текущее сообщение.
        try:
            from aiogram.types import ReactionTypeEmoji

            await self.bot.set_message_reaction(
                self.chat.id, self.message_id, [ReactionTypeEmoji(emoji=emoji)]
            )
            return True
        except Exception:
            return False

    # ==========================================================================
    # REPLY MESSAGE
    # ==========================================================================

    async def get_reply_message(self) -> Optional["AiogramContext"]:
        """Return the message being replied to, wrapped in a new context.

        Returns:
            A new ``AiogramContext`` wrapping ``raw.reply_to_message``, or
            ``None`` if the message is not a reply.

        Example::

            if ctx.is_reply:
                replied_ctx = await ctx.get_reply_message()
                print(replied_ctx.text)
        """
        # RU: Возвращает контекст сообщения, на которое отвечает текущее.
        if self.raw.reply_to_message:
            return AiogramContext(
                self.raw.reply_to_message,
                self.bot,
                command="",
                args=[],
                state=self.state,
            )
        return None

    # ==========================================================================
    # MEDIA DOWNLOAD
    # ==========================================================================

    async def download_media(self, path: Optional[str] = None) -> Optional[str]:
        """Download the media attachment of the current message to disk.

        Selects the best available ``file_id`` (largest photo size for photos)
        and downloads via ``Bot.download_file``.

        Args:
            path: Destination file path. Defaults to ``"downloads/<file_id>"``.

        Returns:
            The destination path string on success, or ``None`` if the message
            has no downloadable media.

        Example::

            saved_path = await ctx.download_media("/tmp/photo.jpg")
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
        """Send a ``typing`` chat action indicator to the current chat.

        Example::

            await ctx.typing()
        """
        # RU: Показывает индикатор «печатает…» в текущем чате.
        await self.bot.send_chat_action(self.chat.id, "typing")

    async def upload_photo(self):
        """Send an ``upload_photo`` chat action indicator to the current chat.

        Example::

            await ctx.upload_photo()
        """
        # RU: Показывает индикатор загрузки фото в текущем чате.
        await self.bot.send_chat_action(self.chat.id, "upload_photo")

    async def upload_video(self):
        """Send an ``upload_video`` chat action indicator to the current chat.

        Example::

            await ctx.upload_video()
        """
        # RU: Показывает индикатор загрузки видео в текущем чате.
        await self.bot.send_chat_action(self.chat.id, "upload_video")

    async def upload_document(self):
        """Send an ``upload_document`` chat action indicator to the current chat.

        Example::

            await ctx.upload_document()
        """
        # RU: Показывает индикатор загрузки документа в текущем чате.
        await self.bot.send_chat_action(self.chat.id, "upload_document")

    async def record_voice(self):
        """Send a ``record_voice`` chat action indicator to the current chat.

        Example::

            await ctx.record_voice()
        """
        # RU: Показывает индикатор записи голосового сообщения в текущем чате.
        await self.bot.send_chat_action(self.chat.id, "record_voice")

    async def record_video(self):
        """Send a ``record_video`` chat action indicator to the current chat.

        Example::

            await ctx.record_video()
        """
        # RU: Показывает индикатор записи видео в текущем чате.
        await self.bot.send_chat_action(self.chat.id, "record_video")

    # ==========================================================================
    # USER/CHAT INFO
    # ==========================================================================

    async def get_chat_member(self, user_id: Optional[int] = None) -> Any:
        """Fetch chat-member status for a user in the current chat.

        Args:
            user_id: Target user ID. Defaults to the sender's ID.

        Returns:
            aiogram ``ChatMember`` object with status and permissions.

        Example::

            member = await ctx.get_chat_member()
            print(member.status)
        """
        # RU: Получает информацию об участнике текущего чата.
        uid = user_id or self.user.id
        return await self.bot.get_chat_member(self.chat.id, uid)

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

    async def ban_user(
        self, user_id: Optional[int] = None, until_date: int = 0
    ) -> bool:
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
            await self.bot.ban_chat_member(
                self.chat.id, uid, until_date=until_date or None
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
        """Create a single ``InlineKeyboardButton``.

        Args:
            text: Button label shown to the user.
            callback_data: Callback data string sent on press. Defaults to
                ``text`` if neither this nor ``url`` is provided.
            url: URL to open on press (mutually exclusive with
                ``callback_data``).

        Returns:
            ``aiogram.types.InlineKeyboardButton`` instance.

        Example::

            btn = AiogramContext.button("Click me", callback_data="btn_1")
        """
        # RU: Создаёт кнопку инлайн-клавиатуры.
        from aiogram.types import InlineKeyboardButton

        if url:
            return InlineKeyboardButton(text=text, url=url)
        return InlineKeyboardButton(text=text, callback_data=callback_data or text)

    @staticmethod
    def keyboard(*rows: List):
        """Build an ``InlineKeyboardMarkup`` from rows of buttons.

        Args:
            *rows: Each positional argument is an iterable of
                ``InlineKeyboardButton`` objects representing one row.

        Returns:
            ``aiogram.types.InlineKeyboardMarkup`` ready to attach as
            ``reply_markup``.

        Example::

            kb = AiogramContext.keyboard(
                [AiogramContext.button("Yes", "yes"), AiogramContext.button("No", "no")]
            )
        """
        # RU: Собирает InlineKeyboardMarkup из строк кнопок.
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
        cache_time: int = 0,
    ) -> bool:
        """Answer a callback query originating from this context.

        Should be called from a callback-query handler to dismiss the loading
        indicator on the button.

        Args:
            text: Optional notification text shown to the user.
            show_alert: If ``True``, show a blocking alert dialog instead of
                a toast notification.
            url: URL to open on the client side (for ``Game`` callbacks).
            cache_time: Seconds the client may cache the answer.

        Returns:
            ``True`` on success, ``False`` if the context has no
            ``answer`` method or if the call failed.

        Example::

            await ctx.answer_callback("Done!", show_alert=False)
        """
        # RU: Отвечает на callback-запрос; снимает индикатор загрузки с кнопки.
        # This is typically called from CallbackQuery handler
        if hasattr(self.raw, "answer"):
            try:
                await self.raw.answer(
                    text=text, show_alert=show_alert, url=url, cache_time=cache_time
                )
                return True
            except Exception:
                pass
        return False
