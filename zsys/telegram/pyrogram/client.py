"""
PyrogramClient - Pyrogram userbot с наследованием от IClient.

PyrogramClient(Client, IClient) — не обёртка, а прямое наследование.
Это значит self IS a pyrogram Client и IS a IClient одновременно.

Иерархия:
    pyrogram.Client          - весь Telegram API
    zsys.core.interfaces.IClient  - интерфейс zsys (start/stop/send_message/is_running)
    PyrogramConfig (BaseConfig)   - конфигурация через Pydantic
    PyrogramClient(Client, IClient) - финальный класс, готовый к наследованию

Наследование в своём боте:
    class MyUserbot(PyrogramClient):
        async def _on_started(self) -> None:
            await self.load_modules()
            await self.send_message("me", "Started!")

        def _register_handlers(self) -> None:
            @self.on_message(filters.command("ping") & filters.me)
            async def ping(_, msg):
                await msg.edit("pong")
"""

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
        ParseMode = None  # monkeygram не имеет ParseMode
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
    """Конфигурация Pyrogram userbot/bot."""

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
        env_prefix = "PYROGRAM_"


# =============================================================================
# CLIENT
# =============================================================================

class PyrogramClient(Client):
    """
    Pyrogram userbot/bot с реализацией IClient (структурная типизация).

    Прямое наследование от pyrogram.Client — все методы Telegram API
    доступны напрямую: self.send_message(), self.on_message(), etc.

    Реализует IClient через duck typing (Protocol structural subtyping):
    isinstance(client, IClient) == True без явного наследования.

    Переопределяй в своём классе:
        _on_started()        — после успешного старта
        _on_stopping()       — перед остановкой
        _register_handlers() — регистрация хендлеров команд
        _load_all_modules()  — загрузка модулей
    """

    def __init__(self, config: PyrogramConfig) -> None:
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

        # Инициализируем pyrogram.Client
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
        return self._is_running

    @property
    def is_stopping(self) -> bool:
        return self._is_stopping

    @property
    def pyrogram_config(self) -> PyrogramConfig:
        return self._zsys_config

    async def start(self) -> None:
        """Запуск клиента с хуком _on_started."""
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
        """Остановка клиента с хуком _on_stopping."""
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
        """Ждёт событий (блокирующий вызов)."""
        await idle()

    # -------------------------------------------------------------------------
    # Хуки для переопределения в подклассах
    # -------------------------------------------------------------------------

    async def _on_started(self) -> None:
        """Вызывается после успешного старта. Переопределяй в своём боте."""
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
        """Вызывается перед загрузкой модулей. Переопределяй для pre-init (i18n, db и т.д.)."""

    async def _on_stopping(self) -> None:
        """Вызывается перед остановкой. Переопределяй в своём боте."""

    def _register_handlers(self) -> None:
        """Регистрация базовых хендлеров. Переопределяй или расширяй."""
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
    # Загрузка модулей (через zsys.modules: ModuleLoader + Router)
    # -------------------------------------------------------------------------

    async def _load_all_modules(self) -> None:
        """
        Загрузка модулей — поддерживает оба формата:

        1. Новый (zsys.modules): @command(ctx: Context) — унифицированные модули.
           Router.attach_pyrogram() подключает все @command() к клиенту.

        2. Старый (pure pyrogram): @Client.on_message(...) — регистрация на уровне
           класса. Работает автоматически при импорте модуля.
        """
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

        # Подключаем @command() хендлеры (новый стиль) к pyrogram клиенту.
        router = get_default_router()
        attach_router(router, self, prefix=cfg.prefix)

        if core_loaded or custom_loaded:
            printer.info("Loaded modules:\n" + self._format_modules(core_loaded, custom_loaded))
        if core_failed or custom_failed:
            printer.warning("Failed modules:\n" + self._format_modules(core_failed, custom_failed))

    @property
    def loaded_modules(self) -> Dict[str, Any]:
        return self._loaded_modules.copy()

    @property
    def failed_modules(self) -> List[str]:
        return self._failed_modules.copy()

    @staticmethod
    def _format_modules(core: List[str], custom: List[str]) -> str:
        """Красивая таблица core | custom модулей (как в оригинале)."""
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
    # Интеграции (API сервер, admin bot)
    # -------------------------------------------------------------------------

    async def _start_integrations(self) -> None:
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
    # Утилиты
    # -------------------------------------------------------------------------

    def _handle_session_error(self) -> None:
        """Переименовывает сломанный файл сессии."""
        try:
            from pathlib import Path
            session_file = Path(self._zsys_config.workdir) / f"{self._zsys_config.session_name}.session"
            if session_file.exists():
                session_file.rename(session_file.with_suffix(".session.old"))
                self._logger.info("Старая сессия переименована в .session.old")
        except Exception as e:
            self._logger.warning(f"Не удалось переименовать сессию: {e}")

    async def _restart(self) -> None:
        """Перезапуск через exec."""
        import sys
        await self.stop()
        os.execv(sys.executable, [sys.executable] + sys.argv)


__all__ = ["PyrogramClient", "PyrogramConfig"]
