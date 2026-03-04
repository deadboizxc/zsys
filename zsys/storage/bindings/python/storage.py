"""
Python cffi bindings for zsys/storage (ZsysKV key-value store).
"""

from typing import Iterator, Tuple

import cffi

_ffi = cffi.FFI()
_ffi.cdef("""
    typedef struct ZsysKV ZsysKV;
    typedef int (*ZsysKVIterFn)(const char *key, const char *value, void *ctx);

    ZsysKV *zsys_kv_new(size_t initial_cap);
    void    zsys_kv_free(ZsysKV *kv);

    int         zsys_kv_set(ZsysKV *kv, const char *key, const char *value);
    const char *zsys_kv_get(ZsysKV *kv, const char *key);
    int         zsys_kv_del(ZsysKV *kv, const char *key);
    int         zsys_kv_has(ZsysKV *kv, const char *key);
    size_t      zsys_kv_count(ZsysKV *kv);
    void        zsys_kv_clear(ZsysKV *kv);
    void        zsys_kv_foreach(ZsysKV *kv, ZsysKVIterFn fn, void *ctx);

    char *zsys_kv_to_json(ZsysKV *kv);
    int   zsys_kv_from_json(ZsysKV *kv, const char *json);

    void zsys_free(void *ptr);
""")

_lib = _ffi.dlopen("libzsys_storage.so")


class KV:
    """Dict-like wrapper around ZsysKV."""

    def __init__(self, initial_cap: int = 0) -> None:
        self._kv = _lib.zsys_kv_new(initial_cap)
        if self._kv == _ffi.NULL:
            raise MemoryError("zsys_kv_new returned NULL")

    def __del__(self) -> None:
        if self._kv != _ffi.NULL:
            _lib.zsys_kv_free(self._kv)
            self._kv = _ffi.NULL

    # ── dict-like interface ────────────────────────────────────────────────

    def __setitem__(self, key: str, value: str) -> None:
        rc = _lib.zsys_kv_set(self._kv, key.encode(), value.encode())
        if rc != 0:
            raise MemoryError(f"zsys_kv_set failed for key {key!r}")

    def __getitem__(self, key: str) -> str:
        ptr = _lib.zsys_kv_get(self._kv, key.encode())
        if ptr == _ffi.NULL:
            raise KeyError(key)
        return _ffi.string(ptr).decode()

    def __delitem__(self, key: str) -> None:
        rc = _lib.zsys_kv_del(self._kv, key.encode())
        if rc != 0:
            raise KeyError(key)

    def __contains__(self, key: object) -> bool:
        if not isinstance(key, str):
            return False
        return _lib.zsys_kv_has(self._kv, key.encode()) == 1

    def __len__(self) -> int:
        return _lib.zsys_kv_count(self._kv)

    def get(self, key: str, default: str | None = None) -> str | None:
        ptr = _lib.zsys_kv_get(self._kv, key.encode())
        if ptr == _ffi.NULL:
            return default
        return _ffi.string(ptr).decode()

    def clear(self) -> None:
        _lib.zsys_kv_clear(self._kv)

    def items(self) -> list[Tuple[str, str]]:
        result: list[Tuple[str, str]] = []

        @_ffi.callback("int(const char *, const char *, void *)")
        def _cb(key, value, _ctx):
            result.append((_ffi.string(key).decode(), _ffi.string(value).decode()))
            return 0

        _lib.zsys_kv_foreach(self._kv, _cb, _ffi.NULL)
        return result

    def __iter__(self) -> Iterator[str]:
        return iter(k for k, _ in self.items())

    # ── serialisation ─────────────────────────────────────────────────────

    def to_json(self) -> str:
        ptr = _lib.zsys_kv_to_json(self._kv)
        if ptr == _ffi.NULL:
            raise RuntimeError("zsys_kv_to_json failed")
        try:
            return _ffi.string(ptr).decode()
        finally:
            _lib.zsys_free(ptr)

    def from_json(self, json: str) -> None:
        rc = _lib.zsys_kv_from_json(self._kv, json.encode())
        if rc != 0:
            raise ValueError("zsys_kv_from_json: parse or allocation error")
