"""
zsys._ctypes — ctypes bindings for libzsys_core.so.

Loads the shared library at import time and re-exports low-level ctypes
Structure classes plus thin Python wrappers for ZsysUser, ZsysChat,
ZsysClientConfig, and ZsysKV.

This module is portable across CPython versions, PyPy, and any
ctypes-capable runtime — unlike the ``_zsys_core`` CPython extension.

Typical usage::

    from zsys._ctypes import User, Chat, ClientConfig, KV

    user = User()
    user.id = 123456789
    user.username = "deadboizxc"
    print(user.to_json())
"""
# RU: Модуль ctypes-привязок к libzsys_core.so.
# RU: Работает в любом Python-рантайме (PyPy, CPython и др.).

from __future__ import annotations

import ctypes
import os
import sys
from pathlib import Path

__all__ = ["lib", "User", "Chat", "ClientConfig", "KV"]

# ── locate libzsys_core.so ───────────────────────────────────────────────────


def _find_lib() -> ctypes.CDLL:
    """
    Locate and load ``libzsys_core.so`` (or platform equivalent).

    Search order:
    1. ``ZSYS_LIB`` environment variable (full path).
    2. ``build/c/`` relative to the zsys package root (dev mode).
    3. System linker path via ``ctypes.util.find_library``.

    Returns:
        Loaded CDLL handle.

    Raises:
        OSError: If the library cannot be found.
    """
    # RU: Порядок поиска: ZSYS_LIB env → build/c/ → системный путь.
    env_path = os.environ.get("ZSYS_LIB")
    if env_path:
        return ctypes.CDLL(env_path)

    pkg_root = Path(__file__).parent.parent.parent  # zsys repo root
    candidates = [
        pkg_root / "build" / "c" / "libzsys_core.so",
        pkg_root / "build" / "c" / "libzsys_core.dylib",
        pkg_root / "build" / "c" / "libzsys_core.dll",
    ]
    for c in candidates:
        if c.exists():
            return ctypes.CDLL(str(c))

    from ctypes.util import find_library

    name = find_library("zsys_core")
    if name:
        return ctypes.CDLL(name)

    raise OSError(
        "libzsys_core not found. Build it first:\n"
        "  cmake -B build/c && cmake --build build/c\n"
        "or set ZSYS_LIB=/path/to/libzsys_core.so"
    )


try:
    lib: ctypes.CDLL = _find_lib()
    _LIB_AVAILABLE = True
except OSError:
    lib = None  # type: ignore[assignment]
    _LIB_AVAILABLE = False


# ── ZsysUser ctypes wrapper ──────────────────────────────────────────────────


class User:
    """
    Python wrapper around C ``ZsysUser`` struct.

    All fields are read/write Python properties. Memory is managed
    automatically: the underlying C object is freed when the Python
    object is garbage-collected.

    Attributes:
        id (int): Telegram user ID.
        username (str | None): @username without the ``@``.
        first_name (str | None): First name.
        last_name (str | None): Last name.
        phone (str | None): Phone number (E.164 format).
        lang_code (str): Language code (default ``"en"``).
        is_bot (bool): True if user is a bot.
        created_at (int): Unix timestamp of account creation.
    """

    # RU: Python-обёртка над C ZsysUser. Автоматическое управление памятью.

    def __init__(self) -> None:
        """Create a new empty ZsysUser via C library or fallback dataclass."""
        # RU: Создаёт пустой ZsysUser через C-библиотеку или fallback.
        if _LIB_AVAILABLE:
            lib.zsys_user_new.restype = ctypes.c_void_p
            lib.zsys_user_new.argtypes = []
            self._ptr = lib.zsys_user_new()
            if not self._ptr:
                raise MemoryError("zsys_user_new() returned NULL")
        else:
            self._ptr = None
        # Pure-Python fallback fields (always kept in sync for convenience)
        self._id: int = 0
        self._username: str | None = None
        self._first_name: str | None = None
        self._last_name: str | None = None
        self._phone: str | None = None
        self._lang_code: str = "en"
        self._is_bot: bool = False
        self._created_at: int = 0

    def __del__(self) -> None:
        """Free the underlying C ZsysUser."""
        # RU: Освобождает память C-объекта при уничтожении Python-объекта.
        if _LIB_AVAILABLE and self._ptr:
            lib.zsys_user_free.restype = None
            lib.zsys_user_free.argtypes = [ctypes.c_void_p]
            lib.zsys_user_free(self._ptr)
            self._ptr = None

    # ── Properties ──────────────────────────────────────────────────────────

    @property
    def id(self) -> int:
        """Telegram user ID."""
        return self._id

    @id.setter
    def id(self, value: int) -> None:
        self._id = int(value)
        if _LIB_AVAILABLE and self._ptr:
            lib.zsys_user_set_id.restype = None
            lib.zsys_user_set_id.argtypes = [ctypes.c_void_p, ctypes.c_int64]
            lib.zsys_user_set_id(self._ptr, ctypes.c_int64(self._id))

    @property
    def username(self) -> str | None:
        """@username without the @ symbol."""
        return self._username

    @username.setter
    def username(self, value: str | None) -> None:
        self._username = value
        if _LIB_AVAILABLE and self._ptr:
            lib.zsys_user_set_username.restype = None
            lib.zsys_user_set_username.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
            lib.zsys_user_set_username(
                self._ptr,
                value.encode() if value else None,
            )

    @property
    def first_name(self) -> str | None:
        """User first name."""
        return self._first_name

    @first_name.setter
    def first_name(self, value: str | None) -> None:
        self._first_name = value
        if _LIB_AVAILABLE and self._ptr:
            lib.zsys_user_set_first_name.restype = None
            lib.zsys_user_set_first_name.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
            lib.zsys_user_set_first_name(
                self._ptr,
                value.encode() if value else None,
            )

    @property
    def last_name(self) -> str | None:
        """User last name."""
        return self._last_name

    @last_name.setter
    def last_name(self, value: str | None) -> None:
        self._last_name = value
        if _LIB_AVAILABLE and self._ptr:
            lib.zsys_user_set_last_name.restype = None
            lib.zsys_user_set_last_name.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
            lib.zsys_user_set_last_name(
                self._ptr,
                value.encode() if value else None,
            )

    @property
    def phone(self) -> str | None:
        """Phone number in E.164 format."""
        return self._phone

    @phone.setter
    def phone(self, value: str | None) -> None:
        self._phone = value
        if _LIB_AVAILABLE and self._ptr:
            lib.zsys_user_set_phone.restype = None
            lib.zsys_user_set_phone.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
            lib.zsys_user_set_phone(
                self._ptr,
                value.encode() if value else None,
            )

    @property
    def lang_code(self) -> str:
        """Two-letter language code (e.g. 'en', 'ru')."""
        return self._lang_code

    @lang_code.setter
    def lang_code(self, value: str) -> None:
        self._lang_code = value or "en"
        if _LIB_AVAILABLE and self._ptr:
            lib.zsys_user_set_lang_code.restype = None
            lib.zsys_user_set_lang_code.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
            lib.zsys_user_set_lang_code(self._ptr, self._lang_code.encode())

    @property
    def is_bot(self) -> bool:
        """Whether the user is a bot account."""
        return self._is_bot

    @is_bot.setter
    def is_bot(self, value: bool) -> None:
        self._is_bot = bool(value)
        if _LIB_AVAILABLE and self._ptr:
            lib.zsys_user_set_is_bot.restype = None
            lib.zsys_user_set_is_bot.argtypes = [ctypes.c_void_p, ctypes.c_int]
            lib.zsys_user_set_is_bot(self._ptr, int(self._is_bot))

    @property
    def created_at(self) -> int:
        """Unix timestamp of when the account was created."""
        return self._created_at

    @created_at.setter
    def created_at(self, value: int) -> None:
        self._created_at = int(value)
        if _LIB_AVAILABLE and self._ptr:
            lib.zsys_user_set_created_at.restype = None
            lib.zsys_user_set_created_at.argtypes = [ctypes.c_void_p, ctypes.c_int64]
            lib.zsys_user_set_created_at(self._ptr, ctypes.c_int64(self._created_at))

    # ── Serialisation ────────────────────────────────────────────────────────

    def to_json(self) -> str:
        """
        Serialise the user to a JSON string.

        Returns:
            JSON representation of the user.
        """
        # RU: Сериализует пользователя в JSON-строку.
        if _LIB_AVAILABLE and self._ptr:
            lib.zsys_user_to_json.restype = ctypes.c_char_p
            lib.zsys_user_to_json.argtypes = [ctypes.c_void_p]
            result = lib.zsys_user_to_json(self._ptr)
            return result.decode() if result else "{}"
        # Pure Python fallback
        import json

        return json.dumps(
            {
                "id": self._id,
                "username": self._username,
                "first_name": self._first_name,
                "last_name": self._last_name,
                "phone": self._phone,
                "lang_code": self._lang_code,
                "is_bot": self._is_bot,
                "created_at": self._created_at,
            }
        )

    def __repr__(self) -> str:
        return (
            f"User(id={self._id!r}, username={self._username!r}, "
            f"first_name={self._first_name!r})"
        )


# ── ZsysChat ctypes wrapper ──────────────────────────────────────────────────


class Chat:
    """
    Python wrapper around C ``ZsysChat`` struct.

    Attributes:
        id (int): Telegram chat ID.
        type (str): Chat type string (``"private"``, ``"group"``, etc.).
        title (str | None): Chat title or None for private chats.
        username (str | None): Chat @username if public.
        member_count (int): Number of members.
    """

    # RU: Python-обёртка над C ZsysChat.

    TYPES = ("unknown", "private", "group", "supergroup", "channel")

    def __init__(self) -> None:
        """Create a new empty ZsysChat."""
        # RU: Создаёт пустой ZsysChat.
        if _LIB_AVAILABLE:
            lib.zsys_chat_new.restype = ctypes.c_void_p
            lib.zsys_chat_new.argtypes = []
            self._ptr = lib.zsys_chat_new()
            if not self._ptr:
                raise MemoryError("zsys_chat_new() returned NULL")
        else:
            self._ptr = None
        self._id: int = 0
        self._type: str = "unknown"
        self._title: str | None = None
        self._username: str | None = None
        self._member_count: int = 0

    def __del__(self) -> None:
        if _LIB_AVAILABLE and self._ptr:
            lib.zsys_chat_free.restype = None
            lib.zsys_chat_free.argtypes = [ctypes.c_void_p]
            lib.zsys_chat_free(self._ptr)
            self._ptr = None

    @property
    def id(self) -> int:
        return self._id

    @id.setter
    def id(self, value: int) -> None:
        self._id = int(value)
        if _LIB_AVAILABLE and self._ptr:
            lib.zsys_chat_set_id.restype = None
            lib.zsys_chat_set_id.argtypes = [ctypes.c_void_p, ctypes.c_int64]
            lib.zsys_chat_set_id(self._ptr, ctypes.c_int64(self._id))

    @property
    def type(self) -> str:
        return self._type

    @type.setter
    def type(self, value: str) -> None:
        self._type = value if value in self.TYPES else "unknown"
        if _LIB_AVAILABLE and self._ptr:
            lib.zsys_chat_set_type.restype = None
            lib.zsys_chat_set_type.argtypes = [ctypes.c_void_p, ctypes.c_int]
            lib.zsys_chat_set_type(self._ptr, self.TYPES.index(self._type))

    @property
    def title(self) -> str | None:
        return self._title

    @title.setter
    def title(self, value: str | None) -> None:
        self._title = value
        if _LIB_AVAILABLE and self._ptr:
            lib.zsys_chat_set_title.restype = None
            lib.zsys_chat_set_title.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
            lib.zsys_chat_set_title(self._ptr, value.encode() if value else None)

    @property
    def username(self) -> str | None:
        return self._username

    @username.setter
    def username(self, value: str | None) -> None:
        self._username = value
        if _LIB_AVAILABLE and self._ptr:
            lib.zsys_chat_set_username.restype = None
            lib.zsys_chat_set_username.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
            lib.zsys_chat_set_username(self._ptr, value.encode() if value else None)

    @property
    def member_count(self) -> int:
        return self._member_count

    @member_count.setter
    def member_count(self, value: int) -> None:
        self._member_count = int(value)
        if _LIB_AVAILABLE and self._ptr:
            lib.zsys_chat_set_member_count.restype = None
            lib.zsys_chat_set_member_count.argtypes = [ctypes.c_void_p, ctypes.c_int32]
            lib.zsys_chat_set_member_count(self._ptr, self._member_count)

    def to_json(self) -> str:
        """Serialise the chat to JSON."""
        # RU: Сериализует чат в JSON.
        if _LIB_AVAILABLE and self._ptr:
            lib.zsys_chat_to_json.restype = ctypes.c_char_p
            lib.zsys_chat_to_json.argtypes = [ctypes.c_void_p]
            result = lib.zsys_chat_to_json(self._ptr)
            return result.decode() if result else "{}"
        import json

        return json.dumps(
            {
                "id": self._id,
                "type": self._type,
                "title": self._title,
                "username": self._username,
                "member_count": self._member_count,
            }
        )

    def __repr__(self) -> str:
        return f"Chat(id={self._id!r}, type={self._type!r}, title={self._title!r})"


# ── ZsysClientConfig ctypes wrapper ─────────────────────────────────────────


class ClientConfig:
    """
    Python wrapper around C ``ZsysClientConfig`` struct.

    Secrets (``api_hash``, ``bot_token``) are excluded from ``to_json()``
    for security. They are stored in C memory only.

    Attributes:
        api_id (int): Telegram API ID from my.telegram.org.
        api_hash (str | None): Telegram API hash (excluded from JSON output).
        session_name (str): Session file name (without extension).
        phone (str | None): Phone number for user accounts.
        bot_token (str | None): Bot token for bot accounts (excluded from JSON).
        mode (str): ``"user"`` or ``"bot"``.
        lang_code (str): Language code (default ``"en"``).
        device_model (str | None): Device model string.
        app_version (str | None): Application version string.
        sleep_threshold (int): Sleep threshold in seconds (default 60).
        max_concurrent (int): Max concurrent handlers (default 1).
    """

    # RU: Python-обёртка над C ZsysClientConfig.

    def __init__(self) -> None:
        """Create a new ClientConfig with default values."""
        # RU: Создаёт конфиг клиента со значениями по умолчанию.
        if _LIB_AVAILABLE:
            lib.zsys_client_config_new.restype = ctypes.c_void_p
            lib.zsys_client_config_new.argtypes = []
            self._ptr = lib.zsys_client_config_new()
            if not self._ptr:
                raise MemoryError("zsys_client_config_new() returned NULL")
        else:
            self._ptr = None
        self._api_id: int = 0
        self._api_hash: str | None = None
        self._session_name: str = ""
        self._phone: str | None = None
        self._bot_token: str | None = None
        self._mode: str = "user"
        self._lang_code: str = "en"
        self._device_model: str | None = None
        self._app_version: str | None = None
        self._sleep_threshold: int = 60
        self._max_concurrent: int = 1

    def __del__(self) -> None:
        if _LIB_AVAILABLE and self._ptr:
            lib.zsys_client_config_free.restype = None
            lib.zsys_client_config_free.argtypes = [ctypes.c_void_p]
            lib.zsys_client_config_free(self._ptr)
            self._ptr = None

    @property
    def api_id(self) -> int:
        return self._api_id

    @api_id.setter
    def api_id(self, value: int) -> None:
        self._api_id = int(value)
        if _LIB_AVAILABLE and self._ptr:
            lib.zsys_client_set_api_id.restype = None
            lib.zsys_client_set_api_id.argtypes = [ctypes.c_void_p, ctypes.c_int32]
            lib.zsys_client_set_api_id(self._ptr, self._api_id)

    @property
    def api_hash(self) -> str | None:
        return self._api_hash

    @api_hash.setter
    def api_hash(self, value: str | None) -> None:
        self._api_hash = value
        if _LIB_AVAILABLE and self._ptr:
            lib.zsys_client_set_api_hash.restype = None
            lib.zsys_client_set_api_hash.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
            lib.zsys_client_set_api_hash(self._ptr, value.encode() if value else None)

    @property
    def session_name(self) -> str:
        return self._session_name

    @session_name.setter
    def session_name(self, value: str) -> None:
        self._session_name = value or ""
        if _LIB_AVAILABLE and self._ptr:
            lib.zsys_client_set_session_name.restype = None
            lib.zsys_client_set_session_name.argtypes = [
                ctypes.c_void_p,
                ctypes.c_char_p,
            ]
            lib.zsys_client_set_session_name(self._ptr, self._session_name.encode())

    @property
    def phone(self) -> str | None:
        return self._phone

    @phone.setter
    def phone(self, value: str | None) -> None:
        self._phone = value
        if _LIB_AVAILABLE and self._ptr:
            lib.zsys_client_set_phone.restype = None
            lib.zsys_client_set_phone.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
            lib.zsys_client_set_phone(self._ptr, value.encode() if value else None)

    @property
    def bot_token(self) -> str | None:
        return self._bot_token

    @bot_token.setter
    def bot_token(self, value: str | None) -> None:
        self._bot_token = value
        if _LIB_AVAILABLE and self._ptr:
            lib.zsys_client_set_bot_token.restype = None
            lib.zsys_client_set_bot_token.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
            lib.zsys_client_set_bot_token(self._ptr, value.encode() if value else None)

    @property
    def mode(self) -> str:
        return self._mode

    @mode.setter
    def mode(self, value: str) -> None:
        self._mode = value if value in ("user", "bot") else "user"
        if _LIB_AVAILABLE and self._ptr:
            lib.zsys_client_set_mode.restype = None
            lib.zsys_client_set_mode.argtypes = [ctypes.c_void_p, ctypes.c_int]
            lib.zsys_client_set_mode(self._ptr, 0 if self._mode == "user" else 1)

    @property
    def lang_code(self) -> str:
        return self._lang_code

    @lang_code.setter
    def lang_code(self, value: str) -> None:
        self._lang_code = value or "en"
        if _LIB_AVAILABLE and self._ptr:
            lib.zsys_client_set_lang_code.restype = None
            lib.zsys_client_set_lang_code.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
            lib.zsys_client_set_lang_code(self._ptr, self._lang_code.encode())

    @property
    def sleep_threshold(self) -> int:
        return self._sleep_threshold

    @sleep_threshold.setter
    def sleep_threshold(self, value: int) -> None:
        self._sleep_threshold = int(value)
        if _LIB_AVAILABLE and self._ptr:
            lib.zsys_client_set_sleep_threshold.restype = None
            lib.zsys_client_set_sleep_threshold.argtypes = [
                ctypes.c_void_p,
                ctypes.c_int32,
            ]
            lib.zsys_client_set_sleep_threshold(self._ptr, self._sleep_threshold)

    @property
    def max_concurrent(self) -> int:
        return self._max_concurrent

    @max_concurrent.setter
    def max_concurrent(self, value: int) -> None:
        self._max_concurrent = max(1, int(value))
        if _LIB_AVAILABLE and self._ptr:
            lib.zsys_client_set_max_concurrent.restype = None
            lib.zsys_client_set_max_concurrent.argtypes = [
                ctypes.c_void_p,
                ctypes.c_int32,
            ]
            lib.zsys_client_set_max_concurrent(self._ptr, self._max_concurrent)

    def validate(self) -> tuple[bool, str | None]:
        """
        Validate the configuration.

        Returns:
            Tuple of (is_valid: bool, error_message: str | None).
        """
        # RU: Проверяет корректность конфигурации. Возвращает (ok, ошибка).
        if _LIB_AVAILABLE and self._ptr:
            lib.zsys_client_config_validate.restype = ctypes.c_int
            lib.zsys_client_config_validate.argtypes = [
                ctypes.c_void_p,
                ctypes.c_char_p,
                ctypes.c_size_t,
            ]
            buf = ctypes.create_string_buffer(256)
            ok = lib.zsys_client_config_validate(self._ptr, buf, 256)
            return ok == 0, None if ok == 0 else buf.value.decode()
        # Pure Python fallback validation
        if not self._api_id:
            return False, "api_id is required"
        if not self._api_hash:
            return False, "api_hash is required"
        if not self._session_name:
            return False, "session_name is required"
        if self._mode == "user" and not self._phone:
            return False, "phone is required for user mode"
        if self._mode == "bot" and not self._bot_token:
            return False, "bot_token is required for bot mode"
        return True, None

    def to_json(self) -> str:
        """
        Serialise config to JSON, excluding secrets (api_hash, bot_token).

        Returns:
            JSON string with non-secret fields only.
        """
        # RU: Сериализует конфиг в JSON, исключая секреты.
        if _LIB_AVAILABLE and self._ptr:
            lib.zsys_client_config_to_json.restype = ctypes.c_char_p
            lib.zsys_client_config_to_json.argtypes = [ctypes.c_void_p]
            result = lib.zsys_client_config_to_json(self._ptr)
            return result.decode() if result else "{}"
        import json

        return json.dumps(
            {
                "api_id": self._api_id,
                "session_name": self._session_name,
                "phone": self._phone,
                "mode": self._mode,
                "lang_code": self._lang_code,
                "device_model": self._device_model,
                "app_version": self._app_version,
                "sleep_threshold": self._sleep_threshold,
                "max_concurrent": self._max_concurrent,
            }
        )

    def __repr__(self) -> str:
        return (
            f"ClientConfig(api_id={self._api_id!r}, mode={self._mode!r}, "
            f"session={self._session_name!r})"
        )


# ── ZsysKV ctypes wrapper ────────────────────────────────────────────────────


class KV:
    """
    Python wrapper around C ``ZsysKV`` in-memory key-value store.

    Works like a dict with optional JSON serialization via the C library.
    Falls back to a plain Python dict when the C library is unavailable.

    Examples::

        kv = KV()
        kv["user_id"] = "123456"
        print(kv["user_id"])   # "123456"
        print(kv.to_json())    # '{"user_id":"123456"}'
    """

    # RU: Python-обёртка над C ZsysKV. Совместима с dict. Fallback на dict.

    def __init__(self, initial_cap: int = 0) -> None:
        """
        Create a new KV store.

        Args:
            initial_cap: Initial hash-table capacity (0 → C default of 16).
        """
        # RU: Создаёт новое КВ-хранилище.
        if _LIB_AVAILABLE:
            lib.zsys_kv_new.restype = ctypes.c_void_p
            lib.zsys_kv_new.argtypes = [ctypes.c_size_t]
            self._ptr = lib.zsys_kv_new(initial_cap)
            if not self._ptr:
                raise MemoryError("zsys_kv_new() returned NULL")
        else:
            self._ptr = None
            self._fallback: dict[str, str] = {}

    def __del__(self) -> None:
        if _LIB_AVAILABLE and self._ptr:
            lib.zsys_kv_free.restype = None
            lib.zsys_kv_free.argtypes = [ctypes.c_void_p]
            lib.zsys_kv_free(self._ptr)
            self._ptr = None

    def __setitem__(self, key: str, value: str) -> None:
        if _LIB_AVAILABLE and self._ptr:
            lib.zsys_kv_set.restype = ctypes.c_int
            lib.zsys_kv_set.argtypes = [
                ctypes.c_void_p,
                ctypes.c_char_p,
                ctypes.c_char_p,
            ]
            rc = lib.zsys_kv_set(self._ptr, key.encode(), value.encode())
            if rc != 0:
                raise MemoryError("zsys_kv_set() failed")
        else:
            self._fallback[key] = value

    def __getitem__(self, key: str) -> str:
        result = self.get(key)
        if result is None:
            raise KeyError(key)
        return result

    def __delitem__(self, key: str) -> None:
        if _LIB_AVAILABLE and self._ptr:
            lib.zsys_kv_del.restype = ctypes.c_int
            lib.zsys_kv_del.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
            if lib.zsys_kv_del(self._ptr, key.encode()) != 0:
                raise KeyError(key)
        else:
            del self._fallback[key]

    def __contains__(self, key: object) -> bool:
        if not isinstance(key, str):
            return False
        if _LIB_AVAILABLE and self._ptr:
            lib.zsys_kv_has.restype = ctypes.c_int
            lib.zsys_kv_has.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
            return bool(lib.zsys_kv_has(self._ptr, key.encode()))
        return key in self._fallback

    def __len__(self) -> int:
        if _LIB_AVAILABLE and self._ptr:
            lib.zsys_kv_count.restype = ctypes.c_size_t
            lib.zsys_kv_count.argtypes = [ctypes.c_void_p]
            return lib.zsys_kv_count(self._ptr)
        return len(self._fallback)

    def get(self, key: str, default: str | None = None) -> str | None:
        """
        Return the value for key, or default if not found.

        Args:
            key: Key to look up.
            default: Returned when key is absent (default None).
        """
        # RU: Возвращает значение по ключу или default.
        if _LIB_AVAILABLE and self._ptr:
            lib.zsys_kv_get.restype = ctypes.c_char_p
            lib.zsys_kv_get.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
            result = lib.zsys_kv_get(self._ptr, key.encode())
            return result.decode() if result is not None else default
        return self._fallback.get(key, default)

    def clear(self) -> None:
        """Remove all entries."""
        # RU: Очищает хранилище.
        if _LIB_AVAILABLE and self._ptr:
            lib.zsys_kv_clear.restype = None
            lib.zsys_kv_clear.argtypes = [ctypes.c_void_p]
            lib.zsys_kv_clear(self._ptr)
        else:
            self._fallback.clear()

    def to_json(self) -> str:
        """
        Serialise the entire store to a JSON object string.

        Returns:
            JSON string like ``{"key1":"val1","key2":"val2"}``.
        """
        # RU: Сериализует хранилище в JSON-объект.
        if _LIB_AVAILABLE and self._ptr:
            lib.zsys_kv_to_json.restype = ctypes.c_char_p
            lib.zsys_kv_to_json.argtypes = [ctypes.c_void_p]
            result = lib.zsys_kv_to_json(self._ptr)
            return result.decode() if result else "{}"
        import json

        return json.dumps(self._fallback)

    def from_json(self, json_str: str) -> None:
        """
        Deserialise a JSON object and merge into this store.

        Args:
            json_str: Flat JSON object string.
        """
        # RU: Десериализует JSON-объект и мёрджит в хранилище.
        if _LIB_AVAILABLE and self._ptr:
            lib.zsys_kv_from_json.restype = ctypes.c_int
            lib.zsys_kv_from_json.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
            rc = lib.zsys_kv_from_json(self._ptr, json_str.encode())
            if rc != 0:
                raise ValueError("zsys_kv_from_json() parse error")
        else:
            import json

            self._fallback.update(json.loads(json_str))

    def __repr__(self) -> str:
        return f"KV(count={len(self)})"
