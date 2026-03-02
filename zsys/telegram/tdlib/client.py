"""TdlibClient — IClient implementation backed by libtg (TDLib C wrapper).

Provides the same zsys lifecycle interface as PyrogramClient but uses
libtg.so under the hood — no Python Telegram library dependency.

Example::

    from zsys.telegram.tdlib import TdlibClient, TdlibConfig

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

from zsys.core.interfaces.client import IClient
from zsys.core.logging import get_logger
from zsys.telegram.tdlib.config import TdlibConfig
from zsys.telegram.tdlib.binding import (
    libtg,
    TG_ASK_PHONE_FN, TG_ASK_CODE_FN, TG_ASK_PASS_FN,
    TG_READY_FN, TG_ERROR_FN, TG_MESSAGE_FN, TG_RAW_FN,
    TG_FILTER_ALL,
)
from zsys.telegram.tdlib.types import Message

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
        ask_code:  _AskFn = None,
        ask_pass:  _AskFn = None,
    ) -> None:
        self._config   = config
        self._logger   = get_logger(__name__)
        self._loop:    Optional[asyncio.AbstractEventLoop] = None
        self._is_running  = False
        self._is_stopping = False

        # Loaded modules tracking
        self._loaded_modules: Dict[str, Any] = {}
        self._failed_modules: List[str] = []

        # Coroutine auth handlers
        self._ask_phone_coro: _AskFn = ask_phone
        self._ask_code_coro:  _AskFn = ask_code
        self._ask_pass_coro:  _AskFn = ask_pass

        # C callbacks — must be kept alive to prevent GC
        self._c_ask_phone: Any = None
        self._c_ask_code:  Any = None
        self._c_ask_pass:  Any = None
        self._c_on_ready:  Any = None
        self._c_on_error:  Any = None

        # All registered C callback refs (to prevent GC)
        self._handler_refs: List[Any] = []

        # C pointers
        self._cfg_ptr:    Optional[ctypes.c_void_p] = None
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
        self._cfg_ptr = libtg.tg_config_new(
            cfg.api_id,
            cfg.api_hash.encode()
        )
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
            None,
            lambda: libtg.tg_client_wait_ready(self._client_ptr, 120)
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

        self._is_running  = False
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

    async def send_message(self, chat_id: int, text: str,
                           parse_mode: str = "html") -> None:
        """Send a text message to chat_id."""
        libtg.tg_send_text(
            self._client_ptr, chat_id,
            text.encode("utf-8"), parse_mode.encode()
        )

    async def reply(self, msg: Message, text: str,
                    parse_mode: str = "html") -> None:
        """Reply to a message."""
        libtg.tg_reply_text(
            self._client_ptr, msg._ptr,
            text.encode("utf-8"), parse_mode.encode()
        )

    async def edit_message(self, chat_id: int, msg_id: int,
                           text: str, parse_mode: str = "html") -> None:
        libtg.tg_edit_text(
            self._client_ptr, chat_id, msg_id,
            text.encode("utf-8"), parse_mode.encode()
        )

    async def delete_message(self, chat_id: int, msg_id: int) -> None:
        libtg.tg_delete_msg(self._client_ptr, chat_id, msg_id)

    async def send_photo(self, chat_id: int, path: str,
                         caption: str = "") -> None:
        libtg.tg_send_photo(
            self._client_ptr, chat_id,
            path.encode(), caption.encode()
        )

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

    def _register_message_handler(self, fn: Callable, filters: int,
                                   edited: bool = False) -> None:
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

    def _register_raw_handler(self, fn: Callable,
                               update_type: Optional[str]) -> None:
        """Register a raw JSON update handler."""
        client_ref = self

        def _c_raw(c_ptr, json_bytes, ud_ptr):
            json_str = json_bytes.decode("utf-8", errors="replace") if json_bytes else ""
            if asyncio.iscoroutinefunction(fn):
                loop = client_ref._loop
                if loop and loop.is_running():
                    asyncio.run_coroutine_threadsafe(
                        fn(client_ref, json_str), loop)
            else:
                try:
                    fn(client_ref, json_str)
                except Exception as e:
                    client_ref._logger.error(f"Raw handler error: {e}")

        c_fn = TG_RAW_FN(_c_raw)
        self._handler_refs.append(c_fn)
        libtg.tg_on_raw(
            self._client_ptr,
            update_type.encode() if update_type else None,
            c_fn, None
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
                        asyncio.run_coroutine_threadsafe(
                            coro_fn(client_ref), loop)
            return inner

        def _on_ready(c_ptr, ud_ptr):
            loop = client_ref._loop
            if loop and loop.is_running():
                loop.call_soon_threadsafe(client_ref._ready_event.set)

        def _on_error(c_ptr, code, msg_bytes, ud_ptr):
            msg = msg_bytes.decode() if msg_bytes else "unknown"
            client_ref._logger.error(f"Auth error {code}: {msg}")

        self._c_ask_phone = TG_ASK_PHONE_FN(_schedule(self._ask_phone_coro))
        self._c_ask_code  = TG_ASK_CODE_FN(_schedule(self._ask_code_coro))
        self._c_ask_pass  = TG_ASK_PASS_FN(_schedule(self._ask_pass_coro))
        self._c_on_ready  = TG_READY_FN(_on_ready)
        self._c_on_error  = TG_ERROR_FN(_on_error)

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
        raw   = libtg.tg_me_first_name(self._client_ptr)
        name  = raw.decode() if raw else "Unknown"
        self._logger.info(f"Ready as {name} (id={me_id})")

    async def _on_stopping(self) -> None:
        """Called before stop. Override in subclass for cleanup."""
        # RU: Вызывается перед остановкой.

    async def _pre_load_modules(self) -> None:
        """Called before module loading. Override for pre-init."""
        # RU: Вызывается перед загрузкой модулей.

    # ─────────────────────────────────────────────────────────────────────────
    # Module loading (zsys.modules compatible)
    # ─────────────────────────────────────────────────────────────────────────

    async def _load_all_modules(self) -> None:
        """Load zsys modules from core and custom dirs and attach router."""
        # RU: Загрузка модулей — совместима с PyrogramClient.
        from pathlib import Path
        from zsys.modules import get_default_router
        from zsys.modules.loader import ModuleLoader
        from zsys.telegram.tdlib.router import attach_router

        cfg = self._config
        await self._pre_load_modules()

        for dir_path in (cfg.core_modules_dir, cfg.custom_modules_dir):
            p = Path(dir_path)
            if not p.exists():
                continue
            loader = ModuleLoader(p,
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
