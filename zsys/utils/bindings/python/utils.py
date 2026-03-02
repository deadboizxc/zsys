"""Python binding for ZsysUtils via cffi.

Wraps all text / HTML / format utility functions from libzsys_utils.so.

Usage::

    from zsys.utils.bindings.python.utils import ZsysUtils

    u = ZsysUtils()
    print(u.escape_html("<b>hello</b>"))
    print(u.format_bytes(1536))
    chunks = u.split_text("hello world", max_chars=4)
    args   = u.get_args("/cmd foo bar", max_split=-1)
"""

from __future__ import annotations
from pathlib import Path


def _load():
    try:
        from cffi import FFI
        ffi = FFI()
        ffi.cdef("""
            void    zsys_free(char *ptr);

            char   *zsys_escape_html(const char *text, size_t len);
            char   *zsys_strip_html(const char *text, size_t len);
            char   *zsys_truncate_text(const char *text, size_t len,
                        size_t max_chars, const char *suffix);
            char  **zsys_split_text(const char *text, size_t len,
                        size_t max_chars);
            void    zsys_split_free(char **chunks);
            char  **zsys_get_args(const char *text, size_t len, int max_split);

            char   *zsys_format_bytes(int64_t size);
            char   *zsys_format_duration(double seconds);
            char   *zsys_human_time(long seconds, int short_fmt);
            long    zsys_parse_duration(const char *text);

            char   *zsys_format_bold(const char *text, size_t len, int escape);
            char   *zsys_format_italic(const char *text, size_t len, int escape);
            char   *zsys_format_code(const char *text, size_t len, int escape);
            char   *zsys_format_pre(const char *text, size_t len,
                        const char *lang, int escape);
            char   *zsys_format_link(const char *text, size_t tlen,
                        const char *url, size_t ulen, int escape);
            char   *zsys_format_mention(const char *text, size_t len,
                        int64_t user_id, int escape);
            char   *zsys_format_underline(const char *text, size_t len);
            char   *zsys_format_strikethrough(const char *text, size_t len);
            char   *zsys_format_spoiler(const char *text, size_t len);
            char   *zsys_format_quote(const char *text, size_t len);
        """)
        here = Path(__file__).resolve().parent
        for candidate in ["libzsys_utils.so", "libzsys_utils.so.1"]:
            for base in [here, here.parent.parent / "c" / "build",
                         Path("/usr/local/lib"), Path("/usr/lib")]:
                p = base / candidate
                if p.exists():
                    return ffi, ffi.dlopen(str(p))
        return ffi, ffi.dlopen("libzsys_utils.so")
    except Exception as e:
        raise RuntimeError(f"libzsys_utils.so not found: {e}")


def _str(ffi, lib, ptr: object) -> str:
    """Return Python str from a zsys_* heap pointer and free it."""
    if not ptr:
        return ""
    s = ffi.string(ptr).decode()
    lib.zsys_free(ptr)
    return s


def _arr(ffi, lib, pp: object) -> list[str]:
    """Convert a NULL-terminated char** from zsys into a list and free it."""
    if not pp:
        return []
    result: list[str] = []
    i = 0
    while pp[i] != ffi.NULL:
        result.append(ffi.string(pp[i]).decode())
        i += 1
    lib.zsys_split_free(pp)
    return result


class ZsysUtils:
    """High-level Python wrapper for the zsys utils C library."""

    def __init__(self) -> None:
        self._ffi, self._lib = _load()

    # ── text / HTML ─────────────────────────────────────────────────────── #

    def escape_html(self, text: str) -> str:
        """Escape HTML special characters: & < > "."""
        b = text.encode()
        return _str(self._ffi, self._lib,
                    self._lib.zsys_escape_html(b, len(b)))

    def strip_html(self, text: str) -> str:
        """Strip HTML tags and unescape basic entities."""
        b = text.encode()
        return _str(self._ffi, self._lib,
                    self._lib.zsys_strip_html(b, len(b)))

    def truncate(self, text: str, max_chars: int,
                 suffix: str = "…") -> str:
        """Truncate UTF-8 text to max_chars codepoints."""
        b = text.encode()
        s = suffix.encode() if suffix else self._ffi.NULL
        return _str(self._ffi, self._lib,
                    self._lib.zsys_truncate_text(b, len(b), max_chars, s))

    def split_text(self, text: str, max_chars: int = 4096) -> list[str]:
        """Split text into chunks of at most max_chars codepoints each."""
        b = text.encode()
        pp = self._lib.zsys_split_text(b, len(b), max_chars)
        return _arr(self._ffi, self._lib, pp)

    def get_args(self, text: str, max_split: int = -1) -> list[str]:
        """Extract whitespace-split args after the first word."""
        b = text.encode()
        pp = self._lib.zsys_get_args(b, len(b), max_split)
        return _arr(self._ffi, self._lib, pp)

    # ── numeric formatters ───────────────────────────────────────────────── #

    def format_bytes(self, size: int) -> str:
        """Format byte count: "1.5 KB", "3.2 MB" …"""
        return _str(self._ffi, self._lib,
                    self._lib.zsys_format_bytes(size))

    def format_duration(self, seconds: float) -> str:
        """Format seconds as "1h 2m 3s"."""
        return _str(self._ffi, self._lib,
                    self._lib.zsys_format_duration(seconds))

    def human_time(self, seconds: int, short: bool = True) -> str:
        """Format seconds as Russian human time."""
        return _str(self._ffi, self._lib,
                    self._lib.zsys_human_time(seconds, int(short)))

    def parse_duration(self, text: str) -> int:
        """Parse "30m", "1h30m" → total seconds.  Returns -1 on error."""
        return self._lib.zsys_parse_duration(text.encode())

    # ── HTML formatters ──────────────────────────────────────────────────── #

    def bold(self, text: str, escape: bool = True) -> str:
        b = text.encode()
        return _str(self._ffi, self._lib,
                    self._lib.zsys_format_bold(b, len(b), int(escape)))

    def italic(self, text: str, escape: bool = True) -> str:
        b = text.encode()
        return _str(self._ffi, self._lib,
                    self._lib.zsys_format_italic(b, len(b), int(escape)))

    def code(self, text: str, escape: bool = True) -> str:
        b = text.encode()
        return _str(self._ffi, self._lib,
                    self._lib.zsys_format_code(b, len(b), int(escape)))

    def pre(self, text: str, lang: str = "",
            escape: bool = True) -> str:
        b = text.encode()
        l = lang.encode()
        return _str(self._ffi, self._lib,
                    self._lib.zsys_format_pre(b, len(b), l, int(escape)))

    def link(self, text: str, url: str, escape: bool = True) -> str:
        t = text.encode()
        u = url.encode()
        return _str(self._ffi, self._lib,
                    self._lib.zsys_format_link(t, len(t), u, len(u),
                                               int(escape)))

    def mention(self, text: str, user_id: int,
                escape: bool = True) -> str:
        b = text.encode()
        return _str(self._ffi, self._lib,
                    self._lib.zsys_format_mention(b, len(b),
                                                  user_id, int(escape)))

    def underline(self, text: str) -> str:
        b = text.encode()
        return _str(self._ffi, self._lib,
                    self._lib.zsys_format_underline(b, len(b)))

    def strikethrough(self, text: str) -> str:
        b = text.encode()
        return _str(self._ffi, self._lib,
                    self._lib.zsys_format_strikethrough(b, len(b)))

    def spoiler(self, text: str) -> str:
        b = text.encode()
        return _str(self._ffi, self._lib,
                    self._lib.zsys_format_spoiler(b, len(b)))

    def quote(self, text: str) -> str:
        b = text.encode()
        return _str(self._ffi, self._lib,
                    self._lib.zsys_format_quote(b, len(b)))
