"""Python binding for ZsysLog via cffi.

Usage::

    from zsys.log.bindings.python.log import ZsysLog

    log = ZsysLog()
    print(log.ansi_color("hello", "31"))
    print(log.format_json_log("INFO", "started", "2024-01-01T00:00:00Z"))
    print(log.print_box("title", 2))
    print(log.print_separator("─", 40))
    print(log.print_progress(7, 10, 20, "Loading"))
"""

from __future__ import annotations

from pathlib import Path


def _load():
    try:
        from cffi import FFI

        ffi = FFI()
        ffi.cdef("""
            char *zsys_ansi_color(const char *text, const char *code);
            char *zsys_format_json_log(const char *level, const char *message,
                                       const char *ts);
            char *zsys_print_box_str(const char *text, int padding);
            char *zsys_print_separator_str(const char *ch, int length);
            char *zsys_print_progress_str(int current, int total,
                                          const char *prefix, int bar_length);
            void free(void *ptr);
        """)
        here = Path(__file__).resolve().parent
        for candidate in ["libzsys_log.so", "libzsys_log.so.1"]:
            for base in [
                here,
                here.parent.parent / "c" / "build",
                Path("/usr/local/lib"),
                Path("/usr/lib"),
            ]:
                p = base / candidate
                if p.exists():
                    return ffi, ffi.dlopen(str(p))
        return ffi, ffi.dlopen("libzsys_log.so")
    except Exception as e:
        raise RuntimeError(f"libzsys_log.so not found: {e}")


class ZsysLog:
    """High-level Python wrapper for the zsys log/terminal functions."""

    def __init__(self) -> None:
        self._ffi, self._lib = _load()

    def _take(self, ptr) -> str:
        """Decode a heap-allocated C string and free it."""
        if not ptr:
            raise MemoryError("zsys function returned NULL")
        managed = self._ffi.gc(ptr, self._lib.free)
        return self._ffi.string(managed).decode()

    def ansi_color(self, text: str, code: str) -> str:
        """Wrap text with an ANSI escape sequence (e.g. code="31" for red)."""
        return self._take(self._lib.zsys_ansi_color(text.encode(), code.encode()))

    def format_json_log(self, level: str, message: str, timestamp: str) -> str:
        """Format a JSON log line: {\"level\":\"...\",\"message\":\"...\",\"ts\":\"...\"}."""
        return self._take(
            self._lib.zsys_format_json_log(
                level.encode(), message.encode(), timestamp.encode()
            )
        )

    def print_box(self, text: str, padding: int = 1) -> str:
        """Render a Unicode box (╔══╗ style) around text."""
        return self._take(self._lib.zsys_print_box_str(text.encode(), padding))

    def print_separator(self, ch: str, length: int) -> str:
        """Repeat ch length times to build a separator line."""
        return self._take(self._lib.zsys_print_separator_str(ch.encode(), length))

    def print_progress(
        self, current: int, total: int, bar_width: int, prefix: str = ""
    ) -> str:
        """Render a text progress bar: [###---] current/total (N%)."""
        return self._take(
            self._lib.zsys_print_progress_str(
                current, total, prefix.encode(), bar_width
            )
        )
