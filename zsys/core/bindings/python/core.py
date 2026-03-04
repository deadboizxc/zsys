"""
zsys.core Python bindings — wraps libzsys_core.so via cffi.

Usage:
    from zsys.core.bindings.python.core import User, Chat, ClientConfig
"""

import cffi

_ffi = cffi.FFI()

_ffi.cdef("""
/* ── zsys_user.h ─────────────────────────────────────────────────────── */
typedef struct ZsysUser {
    int64_t  id;
    char    *username;
    char    *first_name;
    char    *last_name;
    char    *phone;
    char    *lang_code;
    int      is_bot;
    int      is_premium;
    int64_t  created_at;
} ZsysUser;

ZsysUser *zsys_user_new(void);
void      zsys_user_free(ZsysUser *u);
int       zsys_user_copy(ZsysUser *dst, const ZsysUser *src);
int       zsys_user_set_username(ZsysUser *u, const char *val);
int       zsys_user_set_first_name(ZsysUser *u, const char *val);
int       zsys_user_set_last_name(ZsysUser *u, const char *val);
int       zsys_user_set_phone(ZsysUser *u, const char *val);
int       zsys_user_set_lang_code(ZsysUser *u, const char *val);
char     *zsys_user_to_json(const ZsysUser *u);
int       zsys_user_from_json(ZsysUser *u, const char *json);

/* ── zsys_chat.h ─────────────────────────────────────────────────────── */
typedef enum ZsysChatType {
    ZSYS_CHAT_PRIVATE    = 0,
    ZSYS_CHAT_GROUP      = 1,
    ZSYS_CHAT_SUPERGROUP = 2,
    ZSYS_CHAT_CHANNEL    = 3,
    ZSYS_CHAT_BOT        = 4,
} ZsysChatType;

typedef struct ZsysChat {
    int64_t      id;
    ZsysChatType type;
    char        *title;
    char        *username;
    char        *description;
    int32_t      member_count;
    int          is_restricted;
    int          is_scam;
    int64_t      created_at;
} ZsysChat;

ZsysChat  *zsys_chat_new(void);
void       zsys_chat_free(ZsysChat *c);
int        zsys_chat_copy(ZsysChat *dst, const ZsysChat *src);
int        zsys_chat_set_title(ZsysChat *c, const char *val);
int        zsys_chat_set_username(ZsysChat *c, const char *val);
int        zsys_chat_set_description(ZsysChat *c, const char *val);
const char *zsys_chat_type_str(ZsysChatType type);
char       *zsys_chat_to_json(const ZsysChat *c);
int         zsys_chat_from_json(ZsysChat *c, const char *json);

/* ── zsys_client.h ───────────────────────────────────────────────────── */
typedef enum ZsysClientMode {
    ZSYS_CLIENT_USER = 0,
    ZSYS_CLIENT_BOT  = 1,
} ZsysClientMode;

typedef struct ZsysClientConfig {
    int32_t  api_id;
    char    *api_hash;
    char    *session_name;
    ZsysClientMode mode;
    char    *phone;
    char    *bot_token;
    char    *device_model;
    char    *system_version;
    char    *app_version;
    char    *lang_code;
    char    *lang_pack;
    char    *proxy_host;
    int32_t  proxy_port;
    char    *proxy_user;
    char    *proxy_pass;
    int      sleep_threshold;
    int      max_concurrent;
} ZsysClientConfig;

ZsysClientConfig *zsys_client_config_new(void);
void              zsys_client_config_free(ZsysClientConfig *cfg);
int               zsys_client_config_copy(ZsysClientConfig *dst, const ZsysClientConfig *src);
int               zsys_client_set_api_hash(ZsysClientConfig *c, const char *val);
int               zsys_client_set_session_name(ZsysClientConfig *c, const char *val);
int               zsys_client_set_phone(ZsysClientConfig *c, const char *val);
int               zsys_client_set_bot_token(ZsysClientConfig *c, const char *val);
int               zsys_client_set_device_model(ZsysClientConfig *c, const char *val);
int               zsys_client_set_system_version(ZsysClientConfig *c, const char *val);
int               zsys_client_set_app_version(ZsysClientConfig *c, const char *val);
int               zsys_client_set_lang_code(ZsysClientConfig *c, const char *val);
int               zsys_client_set_lang_pack(ZsysClientConfig *c, const char *val);
int               zsys_client_set_proxy(ZsysClientConfig *c,
                                        const char *host, int32_t port,
                                        const char *user, const char *pass);
int               zsys_client_config_validate(const ZsysClientConfig *c,
                                              char *out_err, size_t err_len);
char             *zsys_client_config_to_json(const ZsysClientConfig *c);
int               zsys_client_config_from_json(ZsysClientConfig *c, const char *json);

/* shared free */
void zsys_free(void *ptr);
""")

_lib = _ffi.dlopen("libzsys_core.so")


def _str(ptr) -> str | None:
    """Decode a C string pointer to Python str, or None."""
    if ptr == _ffi.NULL:
        return None
    return _ffi.string(ptr).decode("utf-8")


# ─────────────────────────── User ────────────────────────────────────────────


class User:
    """Python wrapper for ZsysUser.  Owns the heap allocation."""

    def __init__(self, ptr=None):
        if ptr is None:
            ptr = _lib.zsys_user_new()
            if ptr == _ffi.NULL:
                raise MemoryError("zsys_user_new() returned NULL")
        self._ptr = _ffi.gc(ptr, _lib.zsys_user_free)

    # ── properties ──────────────────────────────────────────────────────────

    @property
    def id(self) -> int:
        return self._ptr.id

    @id.setter
    def id(self, value: int):
        self._ptr.id = value

    @property
    def username(self) -> str | None:
        return _str(self._ptr.username)

    @username.setter
    def username(self, value: str | None):
        _lib.zsys_user_set_username(self._ptr, value.encode() if value else _ffi.NULL)

    @property
    def first_name(self) -> str | None:
        return _str(self._ptr.first_name)

    @first_name.setter
    def first_name(self, value: str):
        _lib.zsys_user_set_first_name(self._ptr, value.encode())

    @property
    def last_name(self) -> str | None:
        return _str(self._ptr.last_name)

    @last_name.setter
    def last_name(self, value: str | None):
        _lib.zsys_user_set_last_name(self._ptr, value.encode() if value else _ffi.NULL)

    @property
    def phone(self) -> str | None:
        return _str(self._ptr.phone)

    @phone.setter
    def phone(self, value: str | None):
        _lib.zsys_user_set_phone(self._ptr, value.encode() if value else _ffi.NULL)

    @property
    def lang_code(self) -> str | None:
        return _str(self._ptr.lang_code)

    @lang_code.setter
    def lang_code(self, value: str | None):
        _lib.zsys_user_set_lang_code(self._ptr, value.encode() if value else _ffi.NULL)

    @property
    def is_bot(self) -> bool:
        return bool(self._ptr.is_bot)

    @is_bot.setter
    def is_bot(self, value: bool):
        self._ptr.is_bot = int(value)

    @property
    def is_premium(self) -> bool:
        return bool(self._ptr.is_premium)

    @is_premium.setter
    def is_premium(self, value: bool):
        self._ptr.is_premium = int(value)

    @property
    def created_at(self) -> int:
        return self._ptr.created_at

    @created_at.setter
    def created_at(self, value: int):
        self._ptr.created_at = value

    # ── serialisation ────────────────────────────────────────────────────────

    def to_json(self) -> str:
        raw = _lib.zsys_user_to_json(self._ptr)
        if raw == _ffi.NULL:
            raise RuntimeError("zsys_user_to_json() failed")
        result = _ffi.string(raw).decode("utf-8")
        _lib.zsys_free(raw)
        return result

    @classmethod
    def from_json(cls, json: str) -> "User":
        obj = cls()
        rc = _lib.zsys_user_from_json(obj._ptr, json.encode())
        if rc != 0:
            raise ValueError("zsys_user_from_json() parse error")
        return obj

    def __repr__(self) -> str:
        return f"User(id={self.id}, username={self.username!r}, first_name={self.first_name!r})"


# ─────────────────────────── ChatType ────────────────────────────────────────


class ChatType:
    PRIVATE = 0
    GROUP = 1
    SUPERGROUP = 2
    CHANNEL = 3
    BOT = 4


# ─────────────────────────── Chat ────────────────────────────────────────────


class Chat:
    """Python wrapper for ZsysChat.  Owns the heap allocation."""

    def __init__(self, ptr=None):
        if ptr is None:
            ptr = _lib.zsys_chat_new()
            if ptr == _ffi.NULL:
                raise MemoryError("zsys_chat_new() returned NULL")
        self._ptr = _ffi.gc(ptr, _lib.zsys_chat_free)

    # ── properties ──────────────────────────────────────────────────────────

    @property
    def id(self) -> int:
        return self._ptr.id

    @id.setter
    def id(self, value: int):
        self._ptr.id = value

    @property
    def type(self) -> int:
        return int(self._ptr.type)

    @type.setter
    def type(self, value: int):
        self._ptr.type = value

    @property
    def type_str(self) -> str:
        return _ffi.string(_lib.zsys_chat_type_str(self._ptr.type)).decode()

    @property
    def title(self) -> str | None:
        return _str(self._ptr.title)

    @title.setter
    def title(self, value: str | None):
        _lib.zsys_chat_set_title(self._ptr, value.encode() if value else _ffi.NULL)

    @property
    def username(self) -> str | None:
        return _str(self._ptr.username)

    @username.setter
    def username(self, value: str | None):
        _lib.zsys_chat_set_username(self._ptr, value.encode() if value else _ffi.NULL)

    @property
    def description(self) -> str | None:
        return _str(self._ptr.description)

    @description.setter
    def description(self, value: str | None):
        _lib.zsys_chat_set_description(
            self._ptr, value.encode() if value else _ffi.NULL
        )

    @property
    def member_count(self) -> int:
        return self._ptr.member_count

    @member_count.setter
    def member_count(self, value: int):
        self._ptr.member_count = value

    @property
    def is_restricted(self) -> bool:
        return bool(self._ptr.is_restricted)

    @is_restricted.setter
    def is_restricted(self, value: bool):
        self._ptr.is_restricted = int(value)

    @property
    def is_scam(self) -> bool:
        return bool(self._ptr.is_scam)

    @is_scam.setter
    def is_scam(self, value: bool):
        self._ptr.is_scam = int(value)

    @property
    def created_at(self) -> int:
        return self._ptr.created_at

    @created_at.setter
    def created_at(self, value: int):
        self._ptr.created_at = value

    # ── serialisation ────────────────────────────────────────────────────────

    def to_json(self) -> str:
        raw = _lib.zsys_chat_to_json(self._ptr)
        if raw == _ffi.NULL:
            raise RuntimeError("zsys_chat_to_json() failed")
        result = _ffi.string(raw).decode("utf-8")
        _lib.zsys_free(raw)
        return result

    @classmethod
    def from_json(cls, json: str) -> "Chat":
        obj = cls()
        rc = _lib.zsys_chat_from_json(obj._ptr, json.encode())
        if rc != 0:
            raise ValueError("zsys_chat_from_json() parse error")
        return obj

    def __repr__(self) -> str:
        return f"Chat(id={self.id}, type={self.type_str!r}, title={self.title!r})"


# ─────────────────────────── ClientMode ──────────────────────────────────────


class ClientMode:
    USER = 0
    BOT = 1


# ─────────────────────────── ClientConfig ────────────────────────────────────


class ClientConfig:
    """Python wrapper for ZsysClientConfig.  Owns the heap allocation."""

    def __init__(self, ptr=None):
        if ptr is None:
            ptr = _lib.zsys_client_config_new()
            if ptr == _ffi.NULL:
                raise MemoryError("zsys_client_config_new() returned NULL")
        self._ptr = _ffi.gc(ptr, _lib.zsys_client_config_free)

    # ── properties ──────────────────────────────────────────────────────────

    @property
    def api_id(self) -> int:
        return self._ptr.api_id

    @api_id.setter
    def api_id(self, value: int):
        self._ptr.api_id = value

    @property
    def api_hash(self) -> str | None:
        return _str(self._ptr.api_hash)

    @api_hash.setter
    def api_hash(self, value: str):
        _lib.zsys_client_set_api_hash(self._ptr, value.encode())

    @property
    def session_name(self) -> str | None:
        return _str(self._ptr.session_name)

    @session_name.setter
    def session_name(self, value: str):
        _lib.zsys_client_set_session_name(self._ptr, value.encode())

    @property
    def mode(self) -> int:
        return int(self._ptr.mode)

    @mode.setter
    def mode(self, value: int):
        self._ptr.mode = value

    @property
    def phone(self) -> str | None:
        return _str(self._ptr.phone)

    @phone.setter
    def phone(self, value: str | None):
        _lib.zsys_client_set_phone(self._ptr, value.encode() if value else _ffi.NULL)

    @property
    def bot_token(self) -> str | None:
        return _str(self._ptr.bot_token)

    @bot_token.setter
    def bot_token(self, value: str | None):
        _lib.zsys_client_set_bot_token(
            self._ptr, value.encode() if value else _ffi.NULL
        )

    @property
    def device_model(self) -> str | None:
        return _str(self._ptr.device_model)

    @device_model.setter
    def device_model(self, value: str | None):
        _lib.zsys_client_set_device_model(
            self._ptr, value.encode() if value else _ffi.NULL
        )

    @property
    def system_version(self) -> str | None:
        return _str(self._ptr.system_version)

    @system_version.setter
    def system_version(self, value: str | None):
        _lib.zsys_client_set_system_version(
            self._ptr, value.encode() if value else _ffi.NULL
        )

    @property
    def app_version(self) -> str | None:
        return _str(self._ptr.app_version)

    @app_version.setter
    def app_version(self, value: str | None):
        _lib.zsys_client_set_app_version(
            self._ptr, value.encode() if value else _ffi.NULL
        )

    @property
    def lang_code(self) -> str | None:
        return _str(self._ptr.lang_code)

    @lang_code.setter
    def lang_code(self, value: str | None):
        _lib.zsys_client_set_lang_code(
            self._ptr, value.encode() if value else _ffi.NULL
        )

    @property
    def lang_pack(self) -> str | None:
        return _str(self._ptr.lang_pack)

    @lang_pack.setter
    def lang_pack(self, value: str | None):
        _lib.zsys_client_set_lang_pack(
            self._ptr, value.encode() if value else _ffi.NULL
        )

    @property
    def proxy_host(self) -> str | None:
        return _str(self._ptr.proxy_host)

    @property
    def proxy_port(self) -> int:
        return self._ptr.proxy_port

    @property
    def proxy_user(self) -> str | None:
        return _str(self._ptr.proxy_user)

    @property
    def proxy_pass(self) -> str | None:
        return _str(self._ptr.proxy_pass)

    def set_proxy(
        self, host: str, port: int, user: str | None = None, password: str | None = None
    ):
        _lib.zsys_client_set_proxy(
            self._ptr,
            host.encode(),
            port,
            user.encode() if user else _ffi.NULL,
            password.encode() if password else _ffi.NULL,
        )

    @property
    def sleep_threshold(self) -> int:
        return self._ptr.sleep_threshold

    @sleep_threshold.setter
    def sleep_threshold(self, value: int):
        self._ptr.sleep_threshold = value

    @property
    def max_concurrent(self) -> int:
        return self._ptr.max_concurrent

    @max_concurrent.setter
    def max_concurrent(self, value: int):
        self._ptr.max_concurrent = value

    # ── validation / serialisation ───────────────────────────────────────────

    def validate(self) -> None:
        """Raise ValueError with a message if required fields are missing."""
        buf = _ffi.new("char[256]")
        rc = _lib.zsys_client_config_validate(self._ptr, buf, 256)
        if rc != 0:
            raise ValueError(_ffi.string(buf).decode("utf-8"))

    def to_json(self) -> str:
        raw = _lib.zsys_client_config_to_json(self._ptr)
        if raw == _ffi.NULL:
            raise RuntimeError("zsys_client_config_to_json() failed")
        result = _ffi.string(raw).decode("utf-8")
        _lib.zsys_free(raw)
        return result

    @classmethod
    def from_json(cls, json: str) -> "ClientConfig":
        obj = cls()
        rc = _lib.zsys_client_config_from_json(obj._ptr, json.encode())
        if rc != 0:
            raise ValueError("zsys_client_config_from_json() parse error")
        return obj

    def __repr__(self) -> str:
        mode = "BOT" if self.mode == ClientMode.BOT else "USER"
        return f"ClientConfig(api_id={self.api_id}, session={self.session_name!r}, mode={mode})"
