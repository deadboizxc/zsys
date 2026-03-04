"""Python binding for ZsysI18n via cffi.

Reads zsys_core.h directly — no manual signature duplication.

Usage::

    from zsys.i18n.bindings.python.i18n import I18n

    t = I18n()
    t.load("en", "/path/to/en.json")
    t.set_lang("en")
    print(t.get("hello"))
"""

from __future__ import annotations

from pathlib import Path


def _load():
    try:
        from cffi import FFI

        ffi = FFI()
        # Parse only the i18n portion of the header
        ffi.cdef("""
            typedef struct ZsysI18n ZsysI18n;
            ZsysI18n   *zsys_i18n_new(void);
            void        zsys_i18n_free(ZsysI18n *i);
            int         zsys_i18n_load_json(ZsysI18n *i,
                            const char *lang_code, const char *json_path);
            void        zsys_i18n_set_lang(ZsysI18n *i, const char *lang_code);
            const char *zsys_i18n_get(ZsysI18n *i, const char *key);
            const char *zsys_i18n_get_lang(ZsysI18n *i,
                            const char *lang_code, const char *key);
        """)
        here = Path(__file__).resolve().parent
        for candidate in ["libzsys_core.so", "libzsys_core.so.1"]:
            for base in [
                here,
                here.parent.parent / "c" / "build",
                Path("/usr/local/lib"),
                Path("/usr/lib"),
            ]:
                p = base / candidate
                if p.exists():
                    return ffi, ffi.dlopen(str(p))
        return ffi, ffi.dlopen("libzsys_core.so")
    except Exception as e:
        raise RuntimeError(f"libzsys_core.so not found: {e}")


class I18n:
    """High-level Python wrapper for ZsysI18n."""

    def __init__(self) -> None:
        self._ffi, self._lib = _load()
        self._ptr = self._lib.zsys_i18n_new()
        if not self._ptr:
            raise MemoryError("zsys_i18n_new returned NULL")

    def __del__(self) -> None:
        if self._ptr:
            self._lib.zsys_i18n_free(self._ptr)
            self._ptr = None

    def load(self, lang_code: str, json_path: str) -> None:
        """Load a JSON locale file for lang_code."""
        rc = self._lib.zsys_i18n_load_json(
            self._ptr, lang_code.encode(), json_path.encode()
        )
        if rc != 0:
            raise FileNotFoundError(f"Failed to load locale: {json_path}")

    def set_lang(self, lang_code: str) -> None:
        """Set the active language."""
        self._lib.zsys_i18n_set_lang(self._ptr, lang_code.encode())

    def get(self, key: str) -> str:
        """Translate key using the active language."""
        r = self._lib.zsys_i18n_get(self._ptr, key.encode())
        return self._ffi.string(r).decode() if r else key

    def get_lang(self, lang_code: str, key: str) -> str:
        """Translate key in a specific language."""
        r = self._lib.zsys_i18n_get_lang(self._ptr, lang_code.encode(), key.encode())
        return self._ffi.string(r).decode() if r else key

    def __call__(self, key: str) -> str:
        """Shortcut: t('key')."""
        return self.get(key)
