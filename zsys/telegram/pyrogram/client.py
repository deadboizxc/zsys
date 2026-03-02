"""PyrogramClient — Pyrogram userbot client with IClient structural subtyping.

Provides ``PyrogramClient`` and ``PyrogramConfig`` as the primary entry-point
for building Pyrogram-based userbots inside the zsys framework.  The client
inherits directly from ``pyrogram.Client`` while satisfying ``IClient``
through structural subtyping (Protocol), giving full Telegram API access
alongside a standardised zsys lifecycle (start / stop / idle).

Note:
    ``PyrogramClient`` is **not** a wrapper around ``pyrogram.Client`` — it
    *is* a ``pyrogram.Client``.  All Telegram API methods (``send_message``,
    ``on_message``, ``get_chat``, …) are available directly on ``self``.
    Subclass and override ``_on_started``, ``_on_stopping``, and
    ``_register_handlers`` to customise behaviour without touching the core.
    The module belongs to the ``zsys.telegram.pyrogram`` subsystem.

Example::

    config = PyrogramConfig(api_id=123456, api_hash="0abc1def")
    client = PyrogramClient(config)
    await client.start()
    await client.idle()
"""
# RU: PyrogramClient — Pyrogram userbot-клиент с реализацией IClient через структурную типизацию.
# RU: Предоставляет PyrogramClient и PyrogramConfig как основную точку входа для Pyrogram-ботов
# RU: в рамках zsys. Клиент наследует pyrogram.Client и удовлетворяет IClient (Protocol).

from __future__ import annotations

import asyncio
import os
from datetime import datetime
from io import IOBase as BinaryIO
from typing import Any, Dict, List, Optional, Union

from pydantic import Field

try:
    from pyrogram import Client, idle, filters, errors
    from pyrogram.types import Message as PyrogramMessage
    try:
        from pyrogram.enums import ParseMode
    except ImportError:
        ParseMode = None  # monkeygram does not have ParseMode
        # RU: monkeygram не имеет ParseMode
    PYROGRAM_AVAILABLE = True
except ImportError:
    PYROGRAM_AVAILABLE = False
    Client = object

from zsys.core.config import BaseConfig
from zsys.core.interfaces.client import IClient
from zsys.core.logging import get_logger
from zsys.core.exceptions import ClientError
from zsys.log import printer


# =============================================================================
# CONFIG
# =============================================================================

class PyrogramConfig(BaseConfig):
    """Configuration for Pyrogram userbot or bot.

    Attributes:
        api_id: Telegram API ID.
        api_hash: Telegram API hash.
        session_name: Session file name on disk.
        session_string: In-memory session string (alternative to file).
        bot_token: Bot token when running as a bot.
        phone_number: Phone number for userbot login.
        app_version: Application version string reported to Telegram.
        device_model: Device model string reported to Telegram.
        system_version: System version string reported to Telegram.
        sleep_threshold: Flood wait sleep threshold in seconds.
        workdir: Working directory for session files.
        prefix: Command prefix character.
        core_modules_dir: Directory for built-in modules.
        custom_modules_dir: Directory for user-defined modules.
        auto_load_modules: Whether to load modules on startup.
        enable_hot_reload: Enable file-system watcher for hot reload.
        hot_reload_dirs: Directories to watch for hot reload.
        enable_api_server: Start an HTTP API server on startup.
        api_server_port: Port for the HTTP API server.
        enable_admin_bot: Start an admin control bot on startup.
        admin_bot_token: Bot token for the admin bot.

    Note:
        All fields can be overridden via environment variables using the
        ``PYROGRAM_`` prefix (e.g. ``PYROGRAM_API_ID``, ``PYROGRAM_API_HASH``).
        This is controlled by the inner ``Config`` class with
        ``env_prefix = "PYROGRAM_"``.

    Example::

        config = PyrogramConfig(api_id=123456, api_hash="0abc1def")
        client = PyrogramClient(config)
    """
    # RU: Конфигурация Pyrogram userbot/bot.
    # RU: Все поля можно переопределить через переменные окружения с префиксом PYROGRAM_.

    # Credentials
    api_id: int = Field(description="Telegram API ID")
    api_hash: str = Field(description="Telegram API Hash")
    session_name: str = Field(default="session", description="Имя файла сессии")
    session_string: Optional[str] = Field(default=None, description="Строка сессии (вместо файла)")
    bot_token: Optional[str] = Field(default=None, description="Bot token (если бот)")
    phone_number: Optional[str] = Field(default=None, description="Номер телефона")

    # App info
    app_version: str = Field(default="1.0.0")
    device_model: str = Field(default="Desktop")
    system_version: str = Field(default="1.0.0")

    # Pyrogram settings
    sleep_threshold: int = Field(default=30)
    workdir: str = Field(default=".")

    # Command prefix
    prefix: str = Field(default=".")

    # Module system
    core_modules_dir: str = Field(default="modules")
    custom_modules_dir: str = Field(default="custom_modules")
    auto_load_modules: bool = Field(default=True)

    # Hot reload
    enable_hot_reload: bool = Field(default=False)
    hot_reload_dirs: list = Field(default_factory=list)

    # Integrations
    enable_api_server: bool = Field(default=False)
    api_server_port: int = Field(default=8000)
    enable_admin_bot: bool = Field(default=False)
    admin_bot_token: str = Field(default="")

    class Config:
        """Pydantic config — sets the ``PYROGRAM_`` env-var prefix for all fields."""
        # RU: Pydantic-конфиг — устанавливает префикс переменных окружения PYROGRAM_.
        env_prefix = "PYROGRAM_"


# =============================================================================
# CLIENT
# =============================================================================

class PyrogramClient(Client):
    """Pyrogram userbot/bot implementing IClient via structural subtyping.

    Inherits directly from ``pyrogram.Client`` so all Telegram API methods are
    available on ``self``: ``self.send_message()``, ``self.on_message()``, etc.

    Satisfies ``IClient`` through duck-typing (Protocol structural subtyping) so
    ``isinstance(client, IClient)`` returns ``True`` without explicit inheritance.

    Attributes:
        is_running: ``True`` while the client is active.
        is_stopping: ``True`` while a graceful shutdown is in progress.
        pyrogram_config: The ``PyrogramConfig`` instance used to init the client.
        loaded_modules: Snapshot dict of successfully loaded module objects.
        failed_modules: List of module names that failed to load.

    Note:
        Override ``_on_started``, ``_on_stopping``, and ``_register_handlers``
        in a subclass to customise lifecycle behaviour without touching the core.

    Example::

        class MyBot(PyrogramClient):
            async def _on_started(self) -> None:
                await self.send_message("me", "Ready!")

        config = PyrogramConfig(api_id=123, api_hash="abc")
        bot = MyBot(config)
        await bot.start()
        await bot.idle()
    """
    # RU: Pyrogram userbot/bot с реализацией IClient через структурную типизацию (Protocol).
    # RU: Наследует pyrogram.Client напрямую — все методы Telegram API доступны через self.

    def __init__(self, config: PyrogramConfig) -> None:
        """Initialize the client with a configuration object.

        Args:
            config: PyrogramConfig instance with all required credentials.

        Raises:
            ImportError: If pyrogram is not installed.
        """
        # RU: Инициализировать клиент с объектом конфигурации.
        if not PYROGRAM_AVAILABLE:
            raise ImportError("pyrogram не установлен")

        self._zsys_config = config
        self._logger = get_logger(__name__)
        self._is_running: bool = False
        self._is_stopping: bool = False
        self._loaded_modules: Dict[str, Any] = {}
        self._failed_modules: List[str] = []
        self._api_server: Optional[Any] = None
        self._admin_bot: Optional[Any] = None

        # Initialize pyrogram.Client with credentials from config
        # RU: Инициализируем pyrogram.Client
        Client.__init__(
            self,
            name=config.session_name,
            api_id=config.api_id,
            api_hash=config.api_hash,
            session_string=config.session_string,
            bot_token=config.bot_token,
            phone_number=config.phone_number,
            app_version=config.app_version,
            device_model=config.device_model,
            system_version=config.system_version,
            workdir=config.workdir,
            sleep_threshold=config.sleep_threshold,
        )

    # -------------------------------------------------------------------------
    # IClient interface
    # -------------------------------------------------------------------------

    @property
    def is_running(self) -> bool:
        """Check whether the client is currently running.

        Returns:
            True if the client has been started and not yet stopped.
        """
        # RU: Проверить, запущен ли клиент в данный момент.
        return self._is_running

    @property
    def is_stopping(self) -> bool:
        """Check whether the client is in the process of stopping.

        Returns:
            True if stop() has been called but has not finished yet.
        """
        # RU: Проверить, находится ли клиент в процессе остановки.
        return self._is_stopping

    @property
    def pyrogram_config(self) -> PyrogramConfig:
        """Return the active configuration object.

        Returns:
            The PyrogramConfig instance used to initialize this client.
        """
        # RU: Вернуть активный объект конфигурации.
        return self._zsys_config

    async def start(self) -> None:
        """Start the client, register handlers, load modules, and call _on_started.

        Raises:
            errors.NotAcceptable: If the session is invalid.
            errors.Unauthorized: If the session is revoked or expired.
        """
        # RU: Запустить клиент с хуком _on_started.
        try:
            await super().start()
        except (errors.NotAcceptable, errors.Unauthorized) as e:
            self._logger.error(f"{type(e).__name__}: {e}")
            self._handle_session_error()
            raise

        self._is_running = True
        self._register_handlers()

        await self._pre_load_modules()

        if self._zsys_config.auto_load_modules:
            await self._load_all_modules()

        await self._start_integrations()
        await self._on_started()

    async def stop(self) -> None:
        """Stop the client gracefully, calling _on_stopping and stopping integrations.

        Returns immediately if already stopping to prevent double shutdown.
        """
        # RU: Остановка клиента с хуком _on_stopping.
        if self._is_stopping:
            return
        self._is_stopping = True

        await self._on_stopping()
        await self._stop_integrations()

        try:
            await self.send_message("me", "**stopped.**")
        except Exception:
            pass

        await super().stop()
        self._is_running = False

    async def idle(self) -> None:
        """Block until a stop signal is received (wraps pyrogram.idle).

        Use this in the main coroutine to keep the client running.
        """
        # RU: Ждёт событий (блокирующий вызов).
        await idle()

    # -------------------------------------------------------------------------
    # Hooks for overriding in subclasses
    # -------------------------------------------------------------------------
    # RU: Хуки для переопределения в подклассах

    async def _on_started(self) -> None:
        """Called after the client starts successfully. Override in subclass.

        Default implementation sends a startup message to Saved Messages.
        """
        # RU: Вызывается после успешного старта. Переопределяй в своём боте.
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            await self.send_message(
                "me",
                f"**{now}** — запущен!\n"
                f"Модулей: {len(self._loaded_modules)} загружено, "
                f"{len(self._failed_modules)} ошибок",
            )
        except Exception:
            pass

    async def _pre_load_modules(self) -> None:
        """Called before module loading. Override for pre-init tasks (i18n, db, etc.).

        Override this hook to perform setup that must complete before any module loads.
        """
        # RU: Вызывается перед загрузкой модулей. Переопределяй для pre-init (i18n, db и т.д.).

    async def _on_stopping(self) -> None:
        """Called before the client stops. Override in subclass for cleanup logic.

        Override to disconnect databases, save state, or notify external services.
        """
        # RU: Вызывается перед остановкой. Переопределяй в своём боте.

    def _register_handlers(self) -> None:
        """Register built-in command handlers (stop, restart). Override to extend.

        Subclasses can call super()._register_handlers() or replace entirely.
        """
        # RU: Регистрация базовых хендлеров. Переопределяй или расширяй.
        prefix = self._zsys_config.prefix

        @self.on_message(filters.command("stop", prefix) & filters.me)
        async def _stop_cmd(_: PyrogramClient, msg: PyrogramMessage) -> None:
            if not self._is_stopping:
                await msg.delete()
                await self.send_message("me", "**stopping...**")
                asyncio.create_task(self.stop())

        @self.on_message(filters.command("restart", prefix) & filters.me)
        async def _restart_cmd(_: PyrogramClient, msg: PyrogramMessage) -> None:
            await msg.delete()
            await self._restart()

    # -------------------------------------------------------------------------
    # Module loading (via zsys.modules: ModuleLoader + Router)
    # -------------------------------------------------------------------------
    # RU: Загрузка модулей (через zsys.modules: ModuleLoader + Router)

    async def _load_all_modules(self) -> None:
        """Load all modules from core and custom directories.

        Supports two module formats:

        1. New style (zsys.modules): @command(ctx: Context) — unified modules.
           Router.attach_pyrogram() connects all @command() handlers to the client.

        2. Old style (pure pyrogram): @Client.on_message(...) — class-level
           registration. Works automatically when the module is imported.
        """
        # RU: Загрузка модулей — поддерживает оба формата.
        from pathlib import Path
        from zsys.modules import get_default_router
        from zsys.modules.loader import ModuleLoader
        from zsys.telegram.pyrogram.router import attach_router

        cfg = self._zsys_config
        core_path   = Path(cfg.core_modules_dir)
        custom_path = Path(cfg.custom_modules_dir)

        core_loaded:   List[str] = []
        core_failed:   List[str] = []
        custom_loaded: List[str] = []
        custom_failed: List[str] = []

        def _make_on_load(loaded_list: List[str]):
            def _on_load(info):
                if info.module is not None:
                    info.module.app    = self  # type: ignore[attr-defined]
                    info.module.client = self  # type: ignore[attr-defined]
                    handlers_count = 0
                    for obj in vars(info.module).values():
                        if callable(obj) and hasattr(obj, "handlers") and isinstance(obj.handlers, (list, tuple)):
                            for handler, group in obj.handlers:
                                self.add_handler(handler, group)
                                handlers_count += 1
                    printer.info(f"Модуль {info.name} загружен ({handlers_count} handlers)")
                self._loaded_modules[info.name] = info.module
                loaded_list.append(info.name)
            return _on_load

        def _make_on_error(failed_list: List[str]):
            def _on_error(info, exc):
                self._failed_modules.append(info.name)
                failed_list.append(info.name)
                printer.error(f"Ошибка загрузки модуля {info.name}: {exc}")
            return _on_error

        loaders = []
        if core_path.exists():
            loaders.append((
                ModuleLoader(
                    core_path,
                    on_load=_make_on_load(core_loaded),
                    on_error=_make_on_error(core_failed),
                ),
                "core",
            ))
        if custom_path.exists():
            loaders.append((
                ModuleLoader(
                    custom_path,
                    on_load=_make_on_load(custom_loaded),
                    on_error=_make_on_error(custom_failed),
                ),
                "custom",
            ))

        core_count   = len(loaders[0][0].discover()) if loaders and loaders[0][1] == "core" else 0
        custom_count = len(loaders[-1][0].discover()) if len(loaders) > 1 else 0
        printer.info(f"Загрузка {core_count} core и {custom_count} custom модулей...")

        for loader, _ in loaders:
            for name in loader.discover():
                loader.load(name)

        # Attach @command() handlers (new style) to the pyrogram client
        # RU: Подключаем @command() хендлеры (новый стиль) к pyrogram клиенту.
        router = get_default_router()
        attach_router(router, self, prefix=cfg.prefix)

        if core_loaded or custom_loaded:
            printer.info("Loaded modules:\n" + self._format_modules(core_loaded, custom_loaded))
        if core_failed or custom_failed:
            printer.warning("Failed modules:\n" + self._format_modules(core_failed, custom_failed))

    @property
    def loaded_modules(self) -> Dict[str, Any]:
        """Return a snapshot of successfully loaded modules.

        Returns:
            Copy of the loaded modules dict mapping name to module object.
        """
        # RU: Вернуть снимок успешно загруженных модулей.
        return self._loaded_modules.copy()

    @property
    def failed_modules(self) -> List[str]:
        """Return a list of module names that failed to load.

        Returns:
            Copy of the list of failed module names.
        """
        # RU: Вернуть список имён модулей, которые не удалось загрузить.
        return self._failed_modules.copy()

    @staticmethod
    def _format_modules(core: List[str], custom: List[str]) -> str:
        """Format core and custom module lists as a side-by-side table.

        Args:
            core: List of core module names.
            custom: List of custom module names.

        Returns:
            Multi-line string with aligned columns for core and custom modules.
        """
        # RU: Красивая таблица core | custom модулей.
        max_len: int = max((len(m) for m in core + custom), default=0)
        lines: List[str] = [
            f"{'Core'.ljust(max_len)} | Custom",
            "-" * (max_len + 3) + "-" * 7,
        ]
        for c, cu in zip(core, custom):
            lines.append(f"{c.ljust(max_len)} | {cu}")
        if len(core) > len(custom):
            lines.extend(f"{c.ljust(max_len)} |" for c in core[len(custom):])
        else:
            lines.extend(f"{' ' * max_len} | {cu}" for cu in custom[len(core):])
        return "\n".join(lines)

    # -------------------------------------------------------------------------
    # Integrations (API server, admin bot)
    # -------------------------------------------------------------------------
    # RU: Интеграции (API сервер, admin bot)

    async def _start_integrations(self) -> None:
        """Start optional integrations: API server and admin bot if configured.

        Failures are logged as warnings and do not abort startup.
        """
        # RU: Запустить опциональные интеграции: API сервер и admin bot, если настроены.
        cfg = self._zsys_config

        if cfg.enable_api_server:
            try:
                from implementations.api.fastapi import start_api_server
                self._api_server = start_api_server(cfg.workdir, port=cfg.api_server_port)
                self._logger.info(f"API сервер запущен на порту {cfg.api_server_port}")
            except Exception as e:
                self._logger.warning(f"API сервер не запущен: {e}")

        if cfg.enable_admin_bot and cfg.admin_bot_token:
            try:
                from core.admin_bot import start_admin_bot
                self._admin_bot = start_admin_bot(cfg.admin_bot_token, self)
                self._logger.info("Admin bot запущен")
            except Exception as e:
                self._logger.warning(f"Admin bot не запущен: {e}")

    async def _stop_integrations(self) -> None:
        """Stop all running integrations gracefully.

        Errors during shutdown are silently ignored to ensure a clean exit.
        """
        # RU: Остановить все запущенные интеграции gracefully.
        if self._api_server:
            try:
                from implementations.api.fastapi import stop_api_server
                stop_api_server()
            except Exception:
                pass

        if self._admin_bot:
            try:
                from core.admin_bot import stop_admin_bot
                stop_admin_bot()
            except Exception:
                pass

    # -------------------------------------------------------------------------
    # Utilities
    # -------------------------------------------------------------------------
    # RU: Утилиты

    def _handle_session_error(self) -> None:
        """Rename a broken session file to prevent repeated auth failures.

        Appends .old suffix so the next startup prompts for fresh authentication.
        """
        # RU: Переименовывает сломанный файл сессии.
        try:
            from pathlib import Path
            session_file = Path(self._zsys_config.workdir) / f"{self._zsys_config.session_name}.session"
            if session_file.exists():
                session_file.rename(session_file.with_suffix(".session.old"))
                self._logger.info("Старая сессия переименована в .session.old")
        except Exception as e:
            self._logger.warning(f"Не удалось переименовать сессию: {e}")

    async def _restart(self) -> None:
        """Restart the process in-place using os.execv.

        Stops the client then replaces the current process image with a fresh one.
        """
        # RU: Перезапуск через exec.
        import sys
        await self.stop()
        os.execv(sys.executable, [sys.executable] + sys.argv)


__all__ = ["PyrogramClient", "PyrogramConfig"]
