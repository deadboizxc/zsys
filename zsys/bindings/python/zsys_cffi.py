"""Python bindings for libzsys via ctypes.

Provides Router, Registry and I18n wrappers over the libzsys C shared library.
Gracefully degrades: import succeeds even when the library is not available,
but constructing an instance will raise RuntimeError.
"""

import ctypes
import os

# ---------------------------------------------------------------------------
# Library loading
# ---------------------------------------------------------------------------

_lib: ctypes.CDLL | None = None


def _load_lib() -> bool:
    global _lib
    candidates = [
        "libzsys.so",
        "libzsys.so.1",
        "libzsys_core.so",
        "libzsys_core.so.1.0.0",
    ]
    for name in candidates:
        try:
            _lib = ctypes.CDLL(name)
            return True
        except OSError:
            pass

    # Search relative to this file (handles in-tree builds)
    here = os.path.dirname(os.path.abspath(__file__))
    for rel in ("../../../..", "../../..", "../..", ".."):
        path = os.path.join(here, rel, "libzsys.so")
        if os.path.exists(path):
            try:
                _lib = ctypes.CDLL(path)
                return True
            except OSError:
                pass
    return False


_available: bool = _load_lib()


def _require_lib() -> ctypes.CDLL:
    if not _available or _lib is None:
        raise RuntimeError(
            "libzsys shared library not found. Build it with: make build-lib"
        )
    return _lib


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------


class Router:
    """Thin wrapper over ZsysRouter C API (open-addressing hash table)."""

    def __init__(self) -> None:
        lib = _require_lib()
        lib.zsys_router_new.restype = ctypes.c_void_p
        lib.zsys_router_new.argtypes = []
        lib.zsys_router_free.restype = None
        lib.zsys_router_free.argtypes = [ctypes.c_void_p]
        lib.zsys_router_add.restype = ctypes.c_int
        lib.zsys_router_add.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
        lib.zsys_router_remove.restype = ctypes.c_int
        lib.zsys_router_remove.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        lib.zsys_router_lookup.restype = ctypes.c_int
        lib.zsys_router_lookup.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        lib.zsys_router_count.restype = ctypes.c_size_t
        lib.zsys_router_count.argtypes = [ctypes.c_void_p]
        lib.zsys_router_clear.restype = None
        lib.zsys_router_clear.argtypes = [ctypes.c_void_p]
        self._lib = lib
        self._ptr = lib.zsys_router_new()
        if not self._ptr:
            raise MemoryError("zsys_router_new returned NULL")

    def __del__(self) -> None:
        if self._ptr:
            self._lib.zsys_router_free(self._ptr)
            self._ptr = None

    def add(self, trigger: str, handler_id: int) -> int:
        """Add trigger → handler_id mapping. Returns 0 on success."""
        return self._lib.zsys_router_add(self._ptr, trigger.encode(), handler_id)

    def remove(self, trigger: str) -> int:
        """Remove a trigger. Returns 0 on success, -1 if not found."""
        return self._lib.zsys_router_remove(self._ptr, trigger.encode())

    def lookup(self, trigger: str) -> int:
        """Return handler_id for trigger, or -1 if not found (case-insensitive)."""
        return self._lib.zsys_router_lookup(self._ptr, trigger.encode())

    def count(self) -> int:
        """Return number of registered triggers."""
        return int(self._lib.zsys_router_count(self._ptr))

    def clear(self) -> None:
        """Remove all triggers."""
        self._lib.zsys_router_clear(self._ptr)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


class Registry:
    """Thin wrapper over ZsysRegistry C API (name → handler_id + metadata)."""

    def __init__(self) -> None:
        lib = _require_lib()
        lib.zsys_registry_new.restype = ctypes.c_void_p
        lib.zsys_registry_new.argtypes = []
        lib.zsys_registry_free.restype = None
        lib.zsys_registry_free.argtypes = [ctypes.c_void_p]
        lib.zsys_registry_register.restype = ctypes.c_int
        lib.zsys_registry_register.argtypes = [
            ctypes.c_void_p,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_char_p,
        ]
        lib.zsys_registry_unregister.restype = ctypes.c_int
        lib.zsys_registry_unregister.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        lib.zsys_registry_get.restype = ctypes.c_int
        lib.zsys_registry_get.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        lib.zsys_registry_count.restype = ctypes.c_size_t
        lib.zsys_registry_count.argtypes = [ctypes.c_void_p]
        lib.zsys_registry_name_at.restype = ctypes.c_char_p
        lib.zsys_registry_name_at.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
        self._lib = lib
        self._ptr = lib.zsys_registry_new()
        if not self._ptr:
            raise MemoryError("zsys_registry_new returned NULL")

    def __del__(self) -> None:
        if self._ptr:
            self._lib.zsys_registry_free(self._ptr)
            self._ptr = None

    def register(
        self, name: str, handler_id: int, description: str = "", category: str = ""
    ) -> int:
        """Register name → handler_id. Returns 0 on success."""
        return self._lib.zsys_registry_register(
            self._ptr,
            name.encode(),
            handler_id,
            description.encode(),
            category.encode(),
        )

    def unregister(self, name: str) -> int:
        """Unregister by name. Returns 0 on success, -1 if not found."""
        return self._lib.zsys_registry_unregister(self._ptr, name.encode())

    def get(self, name: str) -> int:
        """Return handler_id for name, or -1 if not found."""
        return self._lib.zsys_registry_get(self._ptr, name.encode())

    def count(self) -> int:
        return int(self._lib.zsys_registry_count(self._ptr))

    def name_at(self, i: int) -> str | None:
        """Return the name at index i, or None if out of range."""
        r = self._lib.zsys_registry_name_at(self._ptr, i)
        return r.decode() if r else None


# ---------------------------------------------------------------------------
# I18n
# ---------------------------------------------------------------------------


class I18n:
    """Thin wrapper over ZsysI18n C API (flat JSON loader, multi-language)."""

    def __init__(self) -> None:
        lib = _require_lib()
        lib.zsys_i18n_new.restype = ctypes.c_void_p
        lib.zsys_i18n_new.argtypes = []
        lib.zsys_i18n_free.restype = None
        lib.zsys_i18n_free.argtypes = [ctypes.c_void_p]
        lib.zsys_i18n_load_json.restype = ctypes.c_int
        lib.zsys_i18n_load_json.argtypes = [
            ctypes.c_void_p,
            ctypes.c_char_p,
            ctypes.c_char_p,
        ]
        lib.zsys_i18n_set_lang.restype = None
        lib.zsys_i18n_set_lang.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        lib.zsys_i18n_get.restype = ctypes.c_char_p
        lib.zsys_i18n_get.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        lib.zsys_i18n_get_lang.restype = ctypes.c_char_p
        lib.zsys_i18n_get_lang.argtypes = [
            ctypes.c_void_p,
            ctypes.c_char_p,
            ctypes.c_char_p,
        ]
        self._lib = lib
        self._ptr = lib.zsys_i18n_new()
        if not self._ptr:
            raise MemoryError("zsys_i18n_new returned NULL")

    def __del__(self) -> None:
        if self._ptr:
            self._lib.zsys_i18n_free(self._ptr)
            self._ptr = None

    def load_json(self, lang_code: str, json_path: str) -> int:
        """Load a flat JSON file for lang_code. Returns 0 on success."""
        return self._lib.zsys_i18n_load_json(
            self._ptr, lang_code.encode(), json_path.encode()
        )

    def set_lang(self, lang_code: str) -> None:
        """Set the active language for get()."""
        self._lib.zsys_i18n_set_lang(self._ptr, lang_code.encode())

    def get(self, key: str) -> str:
        """Translate key using the active language; returns key if not found."""
        r = self._lib.zsys_i18n_get(self._ptr, key.encode())
        return r.decode() if r else key

    def get_lang(self, lang_code: str, key: str) -> str:
        """Translate key in a specific language; returns key if not found."""
        r = self._lib.zsys_i18n_get_lang(self._ptr, lang_code.encode(), key.encode())
        return r.decode() if r else key
