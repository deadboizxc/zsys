"""TdlibClient — IClient implementation backed by libtg (TDLib C wrapper).

Provides the same zsys lifecycle interface as PyrogramClient but uses
libtg.so under the hood — no Python Telegram library dependency.

Example::

    from zsys.telegram import TdlibClient, TdlibConfig

    cfg = TdlibConfig(api_id=123456, api_hash="abc123")

    async def ask_phone(client):
        client.provide_phone(input("Phone: "))

    async def ask_code(client):
        client.provide_code(input("Code: "))

    client = TdlibClient(cfg, ask_phone=ask_phone, ask_code=ask_code)
    await client.start()
    await client.idle()
"""
# RU: TdlibClient — реализация IClient через libtg.so. Без Python TG зависимостей.

from __future__ import annotations

import asyncio
import ctypes
from typing import Any, Callable, Coroutine, Dict, List, Optional

from zsys.log import get_logger
from zsys.telegram.binding import (
    TG_ASK_CODE_FN,
    TG_ASK_PASS_FN,
    TG_ASK_PHONE_FN,
    TG_CALLBACK_QUERY_FN,
    TG_CHAT_CB_FN,
    TG_DIALOGS_CB_FN,
    TG_ERROR_FN,
    TG_FILE_CB_FN,
    TG_FILTER_ALL,
    TG_INLINE_QUERY_FN,
    TG_MEMBER_CB_FN,
    TG_MEMBER_EVENT_FN,
    TG_MEMBERS_CB_FN,
    TG_MESSAGE_FN,
    TG_MESSAGES_CB_FN,
    TG_RAW_FN,
    TG_READY_FN,
    TG_RESULT_FN,
    TG_USER_CB_FN,
    libtg,
)
from zsys.telegram.config import TdlibConfig
from zsys.telegram.types import Chat, ChatMember, File, Message, User

# Coroutine-based auth handler type
_AskFn = Optional[Callable[["TdlibClient"], Coroutine[Any, Any, None]]]


class TdlibClient:
    """Telegram userbot/bot client using libtg.so (TDLib C wrapper).

    Satisfies IClient through structural subtyping (duck typing).

    Attributes:
        is_running: True while the client is active.
        is_stopping: True during graceful shutdown.
        config: The TdlibConfig instance.

    Args:
        config: TdlibConfig with credentials and settings.
        ask_phone: Async coroutine called when phone number is needed.
        ask_code:  Async coroutine called when auth code is needed.
        ask_pass:  Async coroutine called when 2FA password is needed.

    Note:
        ask_phone / ask_code / ask_pass receive the client instance.
        Call client.provide_phone() / provide_code() / provide_pass()
        inside these coroutines to supply the credentials.

    Example::

        async def on_phone(client):
            client.provide_phone(input("Phone: "))

        client = TdlibClient(cfg, ask_phone=on_phone)
    """

    # RU: TdlibClient — обёртка над C libtg. Реализует IClient без pyrogram.

    def __init__(
        self,
        config: TdlibConfig,
        ask_phone: _AskFn = None,
        ask_code: _AskFn = None,
        ask_pass: _AskFn = None,
    ) -> None:
        self._config = config
        self._logger = get_logger(__name__)
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._is_running = False
        self._is_stopping = False

        # Loaded modules tracking
        self._loaded_modules: Dict[str, Any] = {}
        self._failed_modules: List[str] = []

        # Coroutine auth handlers
        self._ask_phone_coro: _AskFn = ask_phone
        self._ask_code_coro: _AskFn = ask_code
        self._ask_pass_coro: _AskFn = ask_pass

        # C callbacks — must be kept alive to prevent GC
        self._c_ask_phone: Any = None
        self._c_ask_code: Any = None
        self._c_ask_pass: Any = None
        self._c_on_ready: Any = None
        self._c_on_error: Any = None

        # All registered C callback refs (to prevent GC)
        self._handler_refs: List[Any] = []

        # C pointers
        self._cfg_ptr: Optional[ctypes.c_void_p] = None
        self._client_ptr: Optional[ctypes.c_void_p] = None

        self._ready_event = asyncio.Event()

    # ─────────────────────────────────────────────────────────────────────────
    # IClient properties
    # ─────────────────────────────────────────────────────────────────────────

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def is_stopping(self) -> bool:
        return self._is_stopping

    @property
    def config(self) -> TdlibConfig:
        return self._config

    # ─────────────────────────────────────────────────────────────────────────
    # Lifecycle
    # ─────────────────────────────────────────────────────────────────────────

    async def start(self) -> None:
        """Start the client, authorize, load modules, call _on_started."""
        # RU: Запуск: создаём C объекты, регистрируем коллбэки, ждём ready.
        self._loop = asyncio.get_running_loop()
        self._ready_event = asyncio.Event()

        cfg = self._config
        self._cfg_ptr = libtg.tg_config_new(cfg.api_id, cfg.api_hash.encode())
        if not self._cfg_ptr:
            raise RuntimeError("tg_config_new returned NULL")

        # Fill optional config fields directly via struct fields
        # (For now we set the most important ones; a full setter API can be added)
        self._client_ptr = libtg.tg_client_new(self._cfg_ptr)
        if not self._client_ptr:
            libtg.tg_config_free(self._cfg_ptr)
            raise RuntimeError("tg_client_new returned NULL")

        self._register_auth_callbacks()

        ret = libtg.tg_client_start(self._client_ptr)
        if ret != 0:
            raise RuntimeError(f"tg_client_start failed: {ret}")

        self._is_running = True

        # Wait for authorization (run blocking C wait in executor)
        await self._loop.run_in_executor(
            None, lambda: libtg.tg_client_wait_ready(self._client_ptr, 120)
        )

        if self._config.auto_load_modules:
            await self._load_all_modules()

        await self._on_started()

    async def stop(self) -> None:
        """Stop the client gracefully."""
        # RU: Остановка клиента.
        if self._is_stopping:
            return
        self._is_stopping = True

        await self._on_stopping()

        if self._client_ptr:
            libtg.tg_client_stop(self._client_ptr)
            libtg.tg_client_free(self._client_ptr)
            self._client_ptr = None

        if self._cfg_ptr:
            libtg.tg_config_free(self._cfg_ptr)
            self._cfg_ptr = None

        self._is_running = False
        self._is_stopping = False

    async def idle(self) -> None:
        """Block until the client is stopped (asyncio-friendly)."""
        # RU: Асинхронный idle — ждём пока клиент работает.
        while self._is_running:
            await asyncio.sleep(0.5)

    # ─────────────────────────────────────────────────────────────────────────
    # Auth responses (call from ask_phone / ask_code / ask_pass)
    # ─────────────────────────────────────────────────────────────────────────

    def provide_phone(self, phone: str) -> None:
        """Supply phone number when requested by ask_phone callback."""
        libtg.tg_client_provide_phone(self._client_ptr, phone.encode())

    def provide_code(self, code: str) -> None:
        """Supply auth code when requested by ask_code callback."""
        libtg.tg_client_provide_code(self._client_ptr, code.encode())

    def provide_pass(self, password: str) -> None:
        """Supply 2FA password when requested by ask_pass callback."""
        libtg.tg_client_provide_pass(self._client_ptr, password.encode())

    # ─────────────────────────────────────────────────────────────────────────
    # Actions (high-level, async-friendly wrappers)
    # ─────────────────────────────────────────────────────────────────────────

    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str = "html",
        reply_to_message_id: int = 0,
        reply_markup: Any = None,
        disable_notification: bool = False,
        disable_web_page_preview: bool = False,
        schedule_date: Optional[int] = None,
    ) -> None:
        """Send a text message with optional reply and keyboard.

        Args:
            chat_id: Target chat ID.
            text: Message text.
            parse_mode: "html", "markdown", or "" for plain text.
            reply_to_message_id: Message ID to reply to (0 = no reply).
            reply_markup: InlineKeyboardMarkup, ReplyKeyboardMarkup, or JSON string.
            disable_notification: Send silently.
            disable_web_page_preview: Disable link previews.
            schedule_date: Unix timestamp to schedule message (optional).
        """
        import json

        # Convert keyboard object to JSON string
        markup_str: Optional[str] = None
        if reply_markup is not None:
            if hasattr(reply_markup, "to_dict"):
                markup_str = json.dumps(reply_markup.to_dict())
            elif isinstance(reply_markup, str):
                markup_str = reply_markup
            elif isinstance(reply_markup, dict):
                markup_str = json.dumps(reply_markup)

        if reply_to_message_id or markup_str:
            libtg.tg_send_text_ex(
                self._client_ptr,
                chat_id,
                text.encode("utf-8"),
                parse_mode.encode(),
                reply_to_message_id,
                markup_str.encode() if markup_str else None,
            )
        else:
            libtg.tg_send_text(
                self._client_ptr, chat_id, text.encode("utf-8"), parse_mode.encode()
            )

    async def reply(
        self,
        msg: Message,
        text: str,
        parse_mode: str = "html",
        reply_markup: Any = None,
        disable_notification: bool = False,
        disable_web_page_preview: bool = False,
    ) -> None:
        """Reply to a message.

        Args:
            msg: Message to reply to.
            text: Reply text.
            parse_mode: "html", "markdown", or "" for plain text.
            reply_markup: Optional keyboard markup.
            disable_notification: Send silently.
            disable_web_page_preview: Disable link previews.
        """
        # Use send_message with reply_to for full keyboard support
        if reply_markup:
            await self.send_message(
                msg.chat_id,
                text,
                parse_mode=parse_mode,
                reply_to_message_id=msg.id,
                reply_markup=reply_markup,
                disable_notification=disable_notification,
                disable_web_page_preview=disable_web_page_preview,
            )
        else:
            libtg.tg_reply_text(
                self._client_ptr, msg._ptr, text.encode("utf-8"), parse_mode.encode()
            )

    async def send_reaction(
        self,
        chat_id: int,
        message_id: int,
        emoji: str = "👍",
        is_big: bool = False,
    ) -> None:
        """Add a reaction to a message.

        Args:
            chat_id: Chat containing the message.
            message_id: Message to react to.
            emoji: Reaction emoji (e.g., "👍", "❤️", "🔥").
            is_big: Use big reaction animation.
        """
        libtg.tg_react(self._client_ptr, chat_id, message_id, emoji.encode("utf-8"))

    async def edit_message(
        self, chat_id: int, msg_id: int, text: str, parse_mode: str = "html"
    ) -> None:
        libtg.tg_edit_text(
            self._client_ptr, chat_id, msg_id, text.encode("utf-8"), parse_mode.encode()
        )

    async def delete_message(self, chat_id: int, msg_id: int) -> None:
        libtg.tg_delete_msg(self._client_ptr, chat_id, msg_id)

    async def send_photo(self, chat_id: int, path: str, caption: str = "") -> None:
        libtg.tg_send_photo(self._client_ptr, chat_id, path.encode(), caption.encode())

    async def send_video(self, chat_id: int, path: str, caption: str = "") -> None:
        """Send a video file."""
        libtg.tg_send_video(self._client_ptr, chat_id, path.encode(), caption.encode())

    async def send_audio(self, chat_id: int, path: str, caption: str = "") -> None:
        """Send an audio file."""
        libtg.tg_send_audio(self._client_ptr, chat_id, path.encode(), caption.encode())

    async def send_document(self, chat_id: int, path: str, caption: str = "") -> None:
        """Send a document file."""
        libtg.tg_send_doc(self._client_ptr, chat_id, path.encode(), caption.encode())

    async def send_animation(self, chat_id: int, path: str, caption: str = "") -> None:
        """Send an animation (GIF)."""
        libtg.tg_send_animation(
            self._client_ptr, chat_id, path.encode(), caption.encode()
        )

    async def send_sticker(self, chat_id: int, file_id_or_path: str) -> None:
        """Send a sticker by file_id (remote) or local path."""
        libtg.tg_send_sticker(self._client_ptr, chat_id, file_id_or_path.encode())

    async def send_voice(self, chat_id: int, path: str, caption: str = "") -> None:
        """Send a voice message."""
        libtg.tg_send_voice(self._client_ptr, chat_id, path.encode(), caption.encode())

    async def send_location(self, chat_id: int, lat: float, lon: float) -> None:
        """Send a location."""
        libtg.tg_send_location(self._client_ptr, chat_id, lat, lon)

    async def send_contact(
        self, chat_id: int, phone: str, first_name: str, last_name: str = ""
    ) -> None:
        """Send a contact."""
        libtg.tg_send_contact(
            self._client_ptr,
            chat_id,
            phone.encode(),
            first_name.encode(),
            last_name.encode(),
        )

    async def send_poll(
        self, chat_id: int, question: str, options: List[str], is_anonymous: bool = True
    ) -> None:
        """Send a poll."""
        import ctypes

        opt_arr = (ctypes.c_char_p * len(options))(*[o.encode() for o in options])
        libtg.tg_send_poll(
            self._client_ptr,
            chat_id,
            question.encode(),
            opt_arr,
            len(options),
            int(is_anonymous),
        )

    async def send_dice(self, chat_id: int, emoji: str = "🎲") -> None:
        """Send a dice/random emoji."""
        libtg.tg_send_dice(self._client_ptr, chat_id, emoji.encode("utf-8"))

    async def send_chat_action(self, chat_id: int, action: str = "typing") -> None:
        """Send a chat action (e.g. 'typing', 'upload_photo')."""
        libtg.tg_send_chat_action(self._client_ptr, chat_id, action.encode())

    async def copy_message(
        self, to_chat_id: int, from_chat_id: int, msg_id: int
    ) -> None:
        """Copy a message (send_copy=True forward — no forward header)."""
        libtg.tg_copy_message(self._client_ptr, to_chat_id, from_chat_id, msg_id)

    async def forward_messages(
        self, to_chat_id: int, from_chat_id: int, msg_ids: List[int]
    ) -> None:
        """Forward messages (with forward header)."""
        for mid in msg_ids:
            libtg.tg_forward(self._client_ptr, to_chat_id, from_chat_id, mid)

    async def edit_message_text(
        self,
        chat_id: int,
        msg_id: int,
        text: str,
        parse_mode: str = "html",
        reply_markup: Optional[str] = None,
    ) -> None:
        """Edit message text."""
        if reply_markup:
            libtg.tg_edit_text_ex(
                self._client_ptr,
                chat_id,
                msg_id,
                text.encode("utf-8"),
                parse_mode.encode(),
                reply_markup.encode(),
            )
        else:
            libtg.tg_edit_text(
                self._client_ptr,
                chat_id,
                msg_id,
                text.encode("utf-8"),
                parse_mode.encode(),
            )

    async def delete_messages(
        self, chat_id: int, msg_ids: List[int], revoke: bool = True
    ) -> None:
        """Delete multiple messages."""
        import ctypes

        arr = (ctypes.c_int64 * len(msg_ids))(*msg_ids)
        libtg.tg_delete_messages(
            self._client_ptr, chat_id, arr, len(msg_ids), int(revoke)
        )

    async def pin_message(
        self, chat_id: int, msg_id: int, disable_notification: bool = False
    ) -> None:
        """Pin a message."""
        libtg.tg_pin_message(
            self._client_ptr, chat_id, msg_id, int(disable_notification)
        )

    async def unpin_message(self, chat_id: int, msg_id: int) -> None:
        """Unpin a specific message."""
        libtg.tg_unpin_message(self._client_ptr, chat_id, msg_id)

    async def unpin_all_messages(self, chat_id: int) -> None:
        """Unpin all messages in a chat."""
        libtg.tg_unpin_all(self._client_ptr, chat_id)

    async def read_chat_history(self, chat_id: int) -> None:
        """Mark all messages in the chat as read."""
        libtg.tg_read_chat(self._client_ptr, chat_id)

    async def read_all_mentions(self, chat_id: int) -> None:
        """Mark all mentions in the chat as read."""
        libtg.tg_read_mentions(self._client_ptr, chat_id)

    # ─────────────────────────────────────────────────────────────────────────
    # Async getters (return awaitables via asyncio.Future)
    # ─────────────────────────────────────────────────────────────────────────

    def _make_future(self):
        """Create a Future tied to the running event loop."""
        # RU: Создаём Future для текущего event loop.
        return self._loop.create_future()

    async def get_chat(self, chat_id: int) -> Chat:
        """Fetch chat info by ID."""
        lib = libtg._load()
        future = self._make_future()

        def _cb(c_ptr, chat_ptr, ud_ptr):
            if chat_ptr:
                result = Chat(lib, chat_ptr)
                self._loop.call_soon_threadsafe(future.set_result, result)
            else:
                self._loop.call_soon_threadsafe(
                    future.set_exception, RuntimeError("get_chat failed")
                )

        c_fn = TG_CHAT_CB_FN(_cb)
        self._handler_refs.append(c_fn)
        libtg.tg_get_chat(self._client_ptr, chat_id, c_fn, None)
        return await future

    async def get_users(self, user_id: int) -> User:
        """Fetch user info by ID (Pyrogram-style name)."""
        lib = libtg._load()
        future = self._make_future()

        def _cb(c_ptr, user_ptr, ud_ptr):
            if user_ptr:
                result = User(lib, user_ptr)
                self._loop.call_soon_threadsafe(future.set_result, result)
            else:
                self._loop.call_soon_threadsafe(
                    future.set_exception, RuntimeError("get_users failed")
                )

        c_fn = TG_USER_CB_FN(_cb)
        self._handler_refs.append(c_fn)
        libtg.tg_get_user(self._client_ptr, user_id, c_fn, None)
        return await future

    async def get_me(self) -> User:
        """Fetch current account info."""
        # RU: Получаем информацию о текущем аккаунте.
        lib = libtg._load()
        me_id = lib.tg_me_id(self._client_ptr)
        return await self.get_users(me_id)

    async def get_chat_member(self, chat_id: int, user_id: int) -> ChatMember:
        """Fetch a specific chat member."""
        lib = libtg._load()
        future = self._make_future()

        def _cb(c_ptr, member_ptr, ud_ptr):
            if member_ptr:
                result = ChatMember(lib, member_ptr)
                self._loop.call_soon_threadsafe(future.set_result, result)
            else:
                self._loop.call_soon_threadsafe(
                    future.set_exception, RuntimeError("get_chat_member failed")
                )

        c_fn = TG_MEMBER_CB_FN(_cb)
        self._handler_refs.append(c_fn)
        libtg.tg_get_member(self._client_ptr, chat_id, user_id, c_fn, None)
        return await future

    async def get_chat_members(
        self, chat_id: int, offset: int = 0, limit: int = 200
    ) -> List[ChatMember]:
        """Fetch list of chat members."""
        lib = libtg._load()
        future = self._make_future()

        def _cb(c_ptr, members_ptr, count, ud_ptr):
            results = []
            for i in range(count):
                elem_ptr = lib.tg_member_at(members_ptr, i)
                if elem_ptr:
                    results.append(ChatMember(lib, elem_ptr))
            self._loop.call_soon_threadsafe(future.set_result, results)

        c_fn = TG_MEMBERS_CB_FN(_cb)
        self._handler_refs.append(c_fn)
        libtg.tg_get_members(self._client_ptr, chat_id, offset, limit, c_fn, None)
        return await future

    async def get_chat_administrators(self, chat_id: int) -> List[ChatMember]:
        """Fetch list of chat administrators."""
        lib = libtg._load()
        future = self._make_future()

        def _cb(c_ptr, members_ptr, count, ud_ptr):
            results = []
            for i in range(count):
                elem_ptr = lib.tg_member_at(members_ptr, i)
                if elem_ptr:
                    results.append(ChatMember(lib, elem_ptr))
            self._loop.call_soon_threadsafe(future.set_result, results)

        c_fn = TG_MEMBERS_CB_FN(_cb)
        self._handler_refs.append(c_fn)
        libtg.tg_get_admins(self._client_ptr, chat_id, c_fn, None)
        return await future

    async def get_messages(self, chat_id: int, msg_ids: List[int]) -> List[Message]:
        """Fetch specific messages by ID list."""
        import ctypes

        lib = libtg._load()
        future = self._make_future()

        def _cb(c_ptr, msgs_ptr, count, ud_ptr):
            results = []
            for i in range(count):
                elem_ptr = lib.tg_message_at(msgs_ptr, i)
                if elem_ptr:
                    results.append(Message(lib, elem_ptr))
            self._loop.call_soon_threadsafe(future.set_result, results)

        c_fn = TG_MESSAGES_CB_FN(_cb)
        self._handler_refs.append(c_fn)
        arr = (ctypes.c_int64 * len(msg_ids))(*msg_ids)
        libtg.tg_get_messages(self._client_ptr, chat_id, arr, len(msg_ids), c_fn, None)
        return await future

    async def get_chat_history(
        self, chat_id: int, offset_id: int = 0, limit: int = 100
    ):
        """Async generator yielding messages in reverse chronological order.

        Matches Pyrogram's ``async for msg in client.get_chat_history(...)``
        pattern.  Fetches in batches of up to ``limit`` until no more remain.

        Example::

            async for msg in client.get_chat_history(-100123456789, limit=500):
                print(msg.text)
        """
        # RU: Генератор истории сообщений, как в Pyrogram.
        lib = libtg._load()
        from_msg_id = offset_id
        batch_size = min(limit, 100)
        fetched = 0

        while fetched < limit:
            future = self._make_future()

            def _cb(c_ptr, msgs_ptr, count, ud_ptr, _future=future, _lib=lib):
                results = []
                for i in range(count):
                    elem_ptr = _lib.tg_message_at(msgs_ptr, i)
                    if elem_ptr:
                        results.append(Message(_lib, elem_ptr))
                self._loop.call_soon_threadsafe(_future.set_result, results)

            c_fn = TG_MESSAGES_CB_FN(_cb)
            self._handler_refs.append(c_fn)
            libtg.tg_get_history(
                self._client_ptr,
                chat_id,
                from_msg_id,
                min(batch_size, limit - fetched),
                c_fn,
                None,
            )
            batch = await future
            if not batch:
                break
            for msg in batch:
                yield msg
                fetched += 1
            from_msg_id = batch[-1].id  # continue from last message

    async def get_dialogs(self, limit: int = 100) -> List[Chat]:
        """Fetch dialog (chat) list."""
        future = self._make_future()
        chats: List[Chat] = []

        def _cb(c_ptr, ids_ptr, count, ud_ptr):
            # ids_ptr points to an int64 array — resolve chats asynchronously
            import ctypes

            ids = []
            if ids_ptr:
                arr = ctypes.cast(ids_ptr, ctypes.POINTER(ctypes.c_int64))
                for i in range(count):
                    ids.append(arr[i])
            self._loop.call_soon_threadsafe(future.set_result, ids)

        c_fn = TG_DIALOGS_CB_FN(_cb)
        self._handler_refs.append(c_fn)
        libtg.tg_get_dialogs(self._client_ptr, limit, c_fn, None)
        chat_ids = await future
        # Resolve each chat id to a Chat object
        for cid in chat_ids:
            try:
                chat = await self.get_chat(cid)
                chats.append(chat)
            except Exception:
                pass
        return chats

    async def resolve_peer(self, peer) -> Chat:
        """Resolve a username or chat ID to a Chat object."""
        lib = libtg._load()
        future = self._make_future()

        def _cb(c_ptr, chat_ptr, ud_ptr):
            if chat_ptr:
                self._loop.call_soon_threadsafe(future.set_result, Chat(lib, chat_ptr))
            else:
                self._loop.call_soon_threadsafe(
                    future.set_exception, RuntimeError(f"Cannot resolve: {peer}")
                )

        c_fn = TG_CHAT_CB_FN(_cb)
        self._handler_refs.append(c_fn)
        if isinstance(peer, str):
            username = peer.lstrip("@")
            libtg.tg_search_public_chat(self._client_ptr, username.encode(), c_fn, None)
        else:
            libtg.tg_get_chat(self._client_ptr, int(peer), c_fn, None)
        return await future

    async def download_media(self, file_id: int, in_memory: bool = False):
        """Download a file by TDLib file_id.

        Returns:
            str: local file path (``in_memory=False``).
            bytes: file content  (``in_memory=True``).
        """
        lib = libtg._load()
        future = self._make_future()

        def _cb(c_ptr, file_ptr, ud_ptr):
            if file_ptr:
                f = File(lib, file_ptr)
                if in_memory and f.local_path:
                    try:
                        with open(f.local_path, "rb") as fh:
                            self._loop.call_soon_threadsafe(
                                future.set_result, fh.read()
                            )
                        return
                    except OSError:
                        pass
                self._loop.call_soon_threadsafe(future.set_result, f.local_path or "")
            else:
                self._loop.call_soon_threadsafe(
                    future.set_exception, RuntimeError("download_media failed")
                )

        c_fn = TG_FILE_CB_FN(_cb)
        self._handler_refs.append(c_fn)
        libtg.tg_get_file(self._client_ptr, file_id, c_fn, None)
        return await future

    # ─────────────────────────────────────────────────────────────────────────
    # Admin
    # ─────────────────────────────────────────────────────────────────────────

    async def ban_chat_member(
        self, chat_id: int, user_id: int, until_date: int = 0
    ) -> None:
        """Ban a member from a chat."""
        libtg.tg_ban_member(self._client_ptr, chat_id, user_id, until_date)

    async def unban_chat_member(self, chat_id: int, user_id: int) -> None:
        """Unban a previously banned member."""
        libtg.tg_unban_member(self._client_ptr, chat_id, user_id)

    async def restrict_chat_member(
        self, chat_id: int, user_id: int, permissions: int, until_date: int = 0
    ) -> None:
        """Restrict a member's permissions."""
        libtg.tg_restrict_member(
            self._client_ptr, chat_id, user_id, permissions, until_date
        )

    async def promote_chat_member(
        self,
        chat_id: int,
        user_id: int,
        *,
        can_manage_chat: bool = False,
        can_post_messages: bool = False,
        can_edit_messages: bool = False,
        can_delete_messages: bool = False,
        can_ban_users: bool = False,
        can_invite_users: bool = False,
        can_pin_messages: bool = False,
        can_promote_members: bool = False,
        can_change_info: bool = False,
        can_manage_video_chats: bool = False,
        is_anonymous: bool = False,
        custom_title: str = "",
    ) -> None:
        """Promote a member to administrator with specific rights."""
        # RU: Повышаем участника до администратора с выбранными правами.
        from zsys.telegram.binding import (
            TG_ADMIN_ANONYMOUS,
            TG_ADMIN_BAN_USERS,
            TG_ADMIN_CHANGE_INFO,
            TG_ADMIN_DELETE_MESSAGES,
            TG_ADMIN_EDIT_MESSAGES,
            TG_ADMIN_INVITE_USERS,
            TG_ADMIN_MANAGE_CHAT,
            TG_ADMIN_MANAGE_VIDEO,
            TG_ADMIN_PIN_MESSAGES,
            TG_ADMIN_POST_MESSAGES,
            TG_ADMIN_PROMOTE_MEMBERS,
        )

        rights = 0
        if can_manage_chat:
            rights |= TG_ADMIN_MANAGE_CHAT
        if can_post_messages:
            rights |= TG_ADMIN_POST_MESSAGES
        if can_edit_messages:
            rights |= TG_ADMIN_EDIT_MESSAGES
        if can_delete_messages:
            rights |= TG_ADMIN_DELETE_MESSAGES
        if can_ban_users:
            rights |= TG_ADMIN_BAN_USERS
        if can_invite_users:
            rights |= TG_ADMIN_INVITE_USERS
        if can_pin_messages:
            rights |= TG_ADMIN_PIN_MESSAGES
        if can_promote_members:
            rights |= TG_ADMIN_PROMOTE_MEMBERS
        if can_change_info:
            rights |= TG_ADMIN_CHANGE_INFO
        if can_manage_video_chats:
            rights |= TG_ADMIN_MANAGE_VIDEO
        if is_anonymous:
            rights |= TG_ADMIN_ANONYMOUS
        libtg.tg_promote_member(
            self._client_ptr,
            chat_id,
            user_id,
            rights,
            custom_title.encode() if custom_title else b"",
        )

    async def set_chat_permissions(self, chat_id: int, permissions: int) -> None:
        """Set default chat member permissions bitmask."""
        libtg.tg_set_chat_permissions(self._client_ptr, chat_id, permissions)

    async def kick_chat_member(self, chat_id: int, user_id: int) -> None:
        """Remove a member (ban + immediate unban)."""
        libtg.tg_kick_member(self._client_ptr, chat_id, user_id)

    # ─────────────────────────────────────────────────────────────────────────
    # Chat management
    # ─────────────────────────────────────────────────────────────────────────

    async def join_chat(self, chat_id: int) -> None:
        """Join a chat or channel."""
        libtg.tg_join_chat(self._client_ptr, chat_id)

    async def leave_chat(self, chat_id: int) -> None:
        """Leave a chat or channel."""
        libtg.tg_leave_chat(self._client_ptr, chat_id)

    async def set_chat_title(self, chat_id: int, title: str) -> None:
        """Set chat title."""
        libtg.tg_set_chat_title(self._client_ptr, chat_id, title.encode())

    async def set_chat_description(self, chat_id: int, description: str) -> None:
        """Set chat description."""
        libtg.tg_set_chat_description(self._client_ptr, chat_id, description.encode())

    async def archive_chats(self, chat_ids: List[int]) -> None:
        """Archive one or more chats."""
        for cid in chat_ids:
            libtg.tg_archive_chat(self._client_ptr, cid)

    async def unarchive_chats(self, chat_ids: List[int]) -> None:
        """Unarchive one or more chats."""
        for cid in chat_ids:
            libtg.tg_unarchive_chat(self._client_ptr, cid)

    async def mute_chat(self, chat_id: int, seconds: int = 0) -> None:
        """Mute (seconds > 0) or unmute (seconds = 0) a chat."""
        libtg.tg_mute_chat(self._client_ptr, chat_id, seconds)

    # ─────────────────────────────────────────────────────────────────────────
    # User management
    # ─────────────────────────────────────────────────────────────────────────

    async def block_user(self, user_id: int) -> None:
        """Block a user."""
        libtg.tg_block_user(self._client_ptr, user_id)

    async def unblock_user(self, user_id: int) -> None:
        """Unblock a user."""
        libtg.tg_unblock_user(self._client_ptr, user_id)

    # ─────────────────────────────────────────────────────────────────────────
    # Account
    # ─────────────────────────────────────────────────────────────────────────

    async def set_username(self, username: str) -> None:
        """Set the account username."""
        libtg.tg_set_username(self._client_ptr, username.encode())

    async def update_profile(
        self,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        bio: Optional[str] = None,
    ) -> None:
        """Update profile name and/or bio."""
        libtg.tg_update_profile(
            self._client_ptr,
            first_name.encode() if first_name else None,
            last_name.encode() if last_name else None,
            bio.encode() if bio else None,
        )

    async def set_profile_photo(self, path: str) -> None:
        """Upload a new profile photo."""
        libtg.tg_set_profile_photo(self._client_ptr, path.encode())

    async def set_online(self, is_online: bool = True) -> None:
        """Set online/offline status."""
        libtg.tg_set_online(self._client_ptr, int(is_online))

    # ─────────────────────────────────────────────────────────────────────────
    # Bot
    # ─────────────────────────────────────────────────────────────────────────

    async def answer_callback_query(
        self,
        query_id: int,
        text: str = "",
        show_alert: bool = False,
        cache_time: int = 0,
    ) -> None:
        """Answer an inline keyboard callback query."""
        libtg.tg_answer_callback_query(
            self._client_ptr, query_id, text.encode(), int(show_alert), cache_time
        )

    def on_callback_query(self, fn: Callable) -> Callable:
        """Decorator: register a callback query handler.

        The function receives ``(client, query_id, from_id, data)``
        and may be async.
        """
        # RU: Регистрируем обработчик callback query.
        client_ref = self

        def _c_handler(c_ptr, query_id, from_id, data_bytes, ud_ptr):
            data = data_bytes.decode() if data_bytes else ""
            if asyncio.iscoroutinefunction(fn):
                loop = client_ref._loop
                if loop and loop.is_running():
                    asyncio.run_coroutine_threadsafe(
                        fn(client_ref, query_id, from_id, data), loop
                    )
            else:
                try:
                    fn(client_ref, query_id, from_id, data)
                except Exception as e:
                    client_ref._logger.error(f"Callback query handler error: {e}")

        c_fn = TG_CALLBACK_QUERY_FN(_c_handler)
        self._handler_refs.append(c_fn)
        libtg.tg_on_callback_query(self._client_ptr, c_fn, None)
        return fn

    def on_inline_query(self, fn: Callable) -> Callable:
        """Decorator: register an inline query handler.

        The function receives ``(client, query_id, from_id, query, offset)``
        and may be async.
        """
        client_ref = self

        def _c_handler(c_ptr, query_id, from_id, query_b, offset_b, ud_ptr):
            query = query_b.decode() if query_b else ""
            offset = offset_b.decode() if offset_b else ""
            if asyncio.iscoroutinefunction(fn):
                loop = client_ref._loop
                if loop and loop.is_running():
                    asyncio.run_coroutine_threadsafe(
                        fn(client_ref, query_id, from_id, query, offset), loop
                    )
            else:
                try:
                    fn(client_ref, query_id, from_id, query, offset)
                except Exception as e:
                    client_ref._logger.error(f"Inline query handler error: {e}")

        c_fn = TG_INLINE_QUERY_FN(_c_handler)
        self._handler_refs.append(c_fn)
        libtg.tg_on_inline_query(self._client_ptr, c_fn, None)
        return fn

    def _register_member_event(self, fn: Callable, is_left: bool) -> None:
        """Register a chat member join/left handler."""
        lib = libtg._load()
        client_ref = self

        def _c_handler(c_ptr, chat_id, user_ptr, ud_ptr):
            user = User(lib, user_ptr) if user_ptr else None
            if asyncio.iscoroutinefunction(fn):
                loop = client_ref._loop
                if loop and loop.is_running():
                    asyncio.run_coroutine_threadsafe(
                        fn(client_ref, chat_id, user), loop
                    )
            else:
                try:
                    fn(client_ref, chat_id, user)
                except Exception as e:
                    client_ref._logger.error(f"Member event handler error: {e}")

        c_fn = TG_MEMBER_EVENT_FN(_c_handler)
        self._handler_refs.append(c_fn)
        if is_left:
            libtg.tg_on_left_chat_member(self._client_ptr, c_fn, None)
        else:
            libtg.tg_on_new_chat_member(self._client_ptr, c_fn, None)

    def on_new_chat_member(self, fn: Callable) -> Callable:
        """Decorator: fired when a user joins a chat.

        The function receives ``(client, chat_id, user)`` and may be async.
        """
        self._register_member_event(fn, is_left=False)
        return fn

    def on_left_chat_member(self, fn: Callable) -> Callable:
        """Decorator: fired when a user leaves or is removed from a chat.

        The function receives ``(client, chat_id, user)`` and may be async.
        """
        self._register_member_event(fn, is_left=True)
        return fn

    # ─────────────────────────────────────────────────────────────────────────
    # Raw invoke
    # ─────────────────────────────────────────────────────────────────────────

    async def invoke(self, json_str: str) -> str:
        """Send a raw TDLib JSON request and await the response.

        Args:
            json_str: TDLib JSON request without ``@extra``.

        Returns:
            Raw TDLib JSON response string.
        """
        # RU: Отправляем произвольный запрос TDLib и ждём ответ.
        future = self._make_future()

        def _cb(c_ptr, json_bytes, ud_ptr):
            result = json_bytes.decode("utf-8", errors="replace") if json_bytes else ""
            self._loop.call_soon_threadsafe(future.set_result, result)

        c_fn = TG_RESULT_FN(_cb)
        self._handler_refs.append(c_fn)
        libtg.tg_invoke(self._client_ptr, json_str.encode(), c_fn, None)
        return await future

    # ─────────────────────────────────────────────────────────────────────────
    # Handler registration (Python-level)
    # ─────────────────────────────────────────────────────────────────────────

    def on_message(self, filters: int = TG_FILTER_ALL):
        """Decorator to register a message handler.

        The decorated function receives (client, Message) arguments.
        It may be a regular function or a coroutine.

        Example::

            @client.on_message(TG_FILTER_INCOMING | TG_FILTER_TEXT)
            async def handler(client, msg):
                await client.reply(msg, "hello!")
        """

        # RU: Декоратор регистрации хендлера сообщений.
        def decorator(fn: Callable) -> Callable:
            self._register_message_handler(fn, filters, edited=False)
            return fn

        return decorator

    def on_edited(self, filters: int = TG_FILTER_ALL):
        """Decorator to register an edited message handler."""

        def decorator(fn: Callable) -> Callable:
            self._register_message_handler(fn, filters, edited=True)
            return fn

        return decorator

    def on_raw(self, update_type: Optional[str] = None):
        """Decorator to register a raw TDLib update handler.

        Example::

            @client.on_raw("updateDeleteMessages")
            def handler(client, json_str):
                print(json_str)
        """

        def decorator(fn: Callable) -> Callable:
            self._register_raw_handler(fn, update_type)
            return fn

        return decorator

    def _register_message_handler(
        self, fn: Callable, filters: int, edited: bool = False
    ) -> None:
        """Register a C-level message handler calling back into Python."""
        # RU: Создаём C-коллбэк и регистрируем в libtg.
        client_ref = self

        def _c_handler(c_ptr, msg_ptr, ud_ptr):
            msg = Message(libtg._load(), msg_ptr)
            if asyncio.iscoroutinefunction(fn):
                loop = client_ref._loop
                if loop and loop.is_running():
                    asyncio.run_coroutine_threadsafe(fn(client_ref, msg), loop)
            else:
                try:
                    fn(client_ref, msg)
                except Exception as e:
                    client_ref._logger.error(f"Handler error: {e}")

        c_fn = TG_MESSAGE_FN(_c_handler)
        self._handler_refs.append(c_fn)  # prevent GC

        reg = libtg.tg_on_edited if edited else libtg.tg_on_message
        reg(self._client_ptr, filters, c_fn, None)

    def _register_raw_handler(self, fn: Callable, update_type: Optional[str]) -> None:
        """Register a raw JSON update handler."""
        client_ref = self

        def _c_raw(c_ptr, json_bytes, ud_ptr):
            json_str = (
                json_bytes.decode("utf-8", errors="replace") if json_bytes else ""
            )
            if asyncio.iscoroutinefunction(fn):
                loop = client_ref._loop
                if loop and loop.is_running():
                    asyncio.run_coroutine_threadsafe(fn(client_ref, json_str), loop)
            else:
                try:
                    fn(client_ref, json_str)
                except Exception as e:
                    client_ref._logger.error(f"Raw handler error: {e}")

        c_fn = TG_RAW_FN(_c_raw)
        self._handler_refs.append(c_fn)
        libtg.tg_on_raw(
            self._client_ptr, update_type.encode() if update_type else None, c_fn, None
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Auth C callbacks
    # ─────────────────────────────────────────────────────────────────────────

    def _register_auth_callbacks(self) -> None:
        """Create and register C auth callbacks that delegate to async coroutines."""
        # RU: C коллбэки для авторизации → asyncio.run_coroutine_threadsafe.
        client_ref = self

        def _schedule(coro_fn: _AskFn):
            def inner(c_ptr, ud_ptr):
                if coro_fn:
                    loop = client_ref._loop
                    if loop and loop.is_running():
                        asyncio.run_coroutine_threadsafe(coro_fn(client_ref), loop)

            return inner

        def _on_ready(c_ptr, ud_ptr):
            loop = client_ref._loop
            if loop and loop.is_running():
                loop.call_soon_threadsafe(client_ref._ready_event.set)

        def _on_error(c_ptr, code, msg_bytes, ud_ptr):
            msg = msg_bytes.decode() if msg_bytes else "unknown"
            client_ref._logger.error(f"Auth error {code}: {msg}")

        self._c_ask_phone = TG_ASK_PHONE_FN(_schedule(self._ask_phone_coro))
        self._c_ask_code = TG_ASK_CODE_FN(_schedule(self._ask_code_coro))
        self._c_ask_pass = TG_ASK_PASS_FN(_schedule(self._ask_pass_coro))
        self._c_on_ready = TG_READY_FN(_on_ready)
        self._c_on_error = TG_ERROR_FN(_on_error)

        libtg.tg_client_set_auth_handlers(
            self._client_ptr,
            self._c_ask_phone,
            self._c_ask_code,
            self._c_ask_pass,
            self._c_on_ready,
            self._c_on_error,
            None,
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Hooks for subclassing
    # ─────────────────────────────────────────────────────────────────────────

    async def _on_started(self) -> None:
        """Called after authorization and module loading. Override in subclass."""
        # RU: Вызывается после успешной авторизации.
        me_id = libtg.tg_me_id(self._client_ptr)
        raw = libtg.tg_me_first_name(self._client_ptr)
        name = raw.decode() if raw else "Unknown"
        self._logger.info(f"Ready as {name} (id={me_id})")

    async def _on_stopping(self) -> None:
        """Called before stop. Override in subclass for cleanup."""
        # RU: Вызывается перед остановкой.

    async def _pre_load_modules(self) -> None:
        """Called before module loading. Override for pre-init."""
        # RU: Вызывается перед загрузкой модулей.

    # ─────────────────────────────────────────────────────────────────────────
    # Extra methods for Pyrogram compatibility
    # ─────────────────────────────────────────────────────────────────────────

    async def get_chat_members_count(self, chat_id: int) -> int:
        """Get count of chat members."""
        chat = await self.get_chat(chat_id)
        return getattr(chat, "member_count", 0)

    async def get_media_group(self, chat_id: int, message_id: int) -> List[Message]:
        """Get all messages in a media group."""
        # TDLib doesn't have a direct API - get message and find related
        messages = await self.get_messages(chat_id, [message_id])
        if not messages:
            return []
        msg = messages[0]
        if not hasattr(msg, "media_group_id") or not msg.media_group_id:
            return [msg]
        # Fetch surrounding messages to find group
        history = await self.get_chat_history(
            chat_id, limit=20, offset_id=message_id + 10
        )
        return [
            m
            for m in history
            if getattr(m, "media_group_id", None) == msg.media_group_id
        ]

    async def send_media_group(
        self, chat_id: int, media: List[Any], **kwargs: Any
    ) -> List[Message]:
        """Send a group of media as album."""
        # Simplified: send each media separately (full impl needs TDLib inputMessageContent array)
        results = []
        for item in media:
            if hasattr(item, "media") and hasattr(item, "type"):
                path = item.media
                if item.type == "photo":
                    await self.send_photo(chat_id, path, getattr(item, "caption", ""))
                elif item.type == "video":
                    await self.send_video(chat_id, path, getattr(item, "caption", ""))
                elif item.type == "document":
                    await self.send_document(
                        chat_id, path, getattr(item, "caption", "")
                    )
        return results

    async def set_administrator_title(
        self, chat_id: int, user_id: int, title: str
    ) -> None:
        """Set custom admin title."""
        libtg.tg_set_admin_title(self._client_ptr, chat_id, user_id, title.encode())

    async def delete_profile_photos(self, photo_ids: List[int]) -> None:
        """Delete profile photos by IDs."""
        for pid in photo_ids:
            libtg.tg_delete_profile_photo(self._client_ptr, pid)

    async def get_current_user(self) -> User:
        """Alias for get_me (compatibility)."""
        return await self.get_me()

    async def get_user(self, user_id: int) -> User:
        """Get user by ID (alias for get_users with single ID)."""
        return await self.get_users(user_id)

    # ─────────────────────────────────────────────────────────────────────────
    # Module loading (zsys.modules compatible)
    # ─────────────────────────────────────────────────────────────────────────

    async def _load_all_modules(self) -> None:
        """Load zsys modules from core and custom dirs and attach router."""
        # RU: Загрузка модулей — совместима с PyrogramClient.
        from pathlib import Path

        from zsys.modules import get_default_router
        from zsys.modules.loader import ModuleLoader
        from zsys.telegram.router import attach_router

        cfg = self._config
        await self._pre_load_modules()

        for dir_path in (cfg.core_modules_dir, cfg.custom_modules_dir):
            p = Path(dir_path)
            if not p.exists():
                continue
            loader = ModuleLoader(
                p,
                on_load=lambda info: self._on_module_loaded(info),
                on_error=lambda info, exc: self._on_module_error(info, exc),
            )
            for name in loader.discover():
                loader.load(name)

        router = get_default_router()
        attach_router(router, self, prefix=cfg.prefix)

    def _on_module_loaded(self, info) -> None:
        self._loaded_modules[info.name] = info.module
        self._logger.debug(f"Module loaded: {info.name}")

    def _on_module_error(self, info, exc: Exception) -> None:
        self._failed_modules.append(info.name)
        self._logger.error(f"Module failed: {info.name}: {exc}")

    @property
    def loaded_modules(self) -> Dict[str, Any]:
        return self._loaded_modules.copy()

    @property
    def failed_modules(self) -> List[str]:
        return self._failed_modules.copy()


__all__ = ["TdlibClient"]
