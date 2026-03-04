"""
zsys modules bindings – Python (cffi)

Wraps ZsysRouter and ZsysRegistry from libzsys_core.so.
"""

from cffi import FFI

_ffi = FFI()

_ffi.cdef("""
    /* ── router ── */
    typedef struct ZsysRouter ZsysRouter;

    ZsysRouter *zsys_router_new(void);
    void        zsys_router_free(ZsysRouter *r);
    int         zsys_router_add(ZsysRouter *r, const char *trigger, int handler_id);
    int         zsys_router_remove(ZsysRouter *r, const char *trigger);
    int         zsys_router_lookup(ZsysRouter *r, const char *trigger);
    size_t      zsys_router_count(ZsysRouter *r);
    void        zsys_router_clear(ZsysRouter *r);

    /* ── registry ── */
    typedef struct ZsysRegistry ZsysRegistry;

    ZsysRegistry *zsys_registry_new(void);
    void          zsys_registry_free(ZsysRegistry *reg);
    int           zsys_registry_register(ZsysRegistry *reg, const char *name,
                                          int handler_id,
                                          const char *description,
                                          const char *category);
    int           zsys_registry_unregister(ZsysRegistry *reg, const char *name);
    int           zsys_registry_get(ZsysRegistry *reg, const char *name);
    int           zsys_registry_info(ZsysRegistry *reg, const char *name,
                                      char *out_desc, size_t desc_len,
                                      char *out_cat,  size_t cat_len);
    size_t        zsys_registry_count(ZsysRegistry *reg);
    const char   *zsys_registry_name_at(ZsysRegistry *reg, size_t i);
""")

_lib = _ffi.dlopen("libzsys_core.so")


class Router:
    """Trigger → handler_id hash table (open-addressing, case-insensitive)."""

    def __init__(self):
        self._ptr = _lib.zsys_router_new()
        if self._ptr == _ffi.NULL:
            raise MemoryError("zsys_router_new() returned NULL")

    def __del__(self):
        if self._ptr != _ffi.NULL:
            _lib.zsys_router_free(self._ptr)
            self._ptr = _ffi.NULL

    def add(self, trigger: str, handler_id: int) -> None:
        """Add or update a trigger → handler_id mapping."""
        rc = _lib.zsys_router_add(self._ptr, trigger.encode(), handler_id)
        if rc != 0:
            raise RuntimeError(f"zsys_router_add failed for trigger {trigger!r}")

    def remove(self, trigger: str) -> bool:
        """Remove a trigger. Returns True if it existed, False otherwise."""
        return _lib.zsys_router_remove(self._ptr, trigger.encode()) == 0

    def lookup(self, trigger: str) -> int:
        """Return handler_id for trigger, or -1 if not found (case-insensitive)."""
        return _lib.zsys_router_lookup(self._ptr, trigger.encode())

    def __len__(self) -> int:
        return _lib.zsys_router_count(self._ptr)

    def clear(self) -> None:
        """Remove all entries."""
        _lib.zsys_router_clear(self._ptr)

    def __contains__(self, trigger: str) -> bool:
        return self.lookup(trigger) != -1

    def __repr__(self) -> str:
        return f"<Router entries={len(self)}>"


class Registry:
    """Dynamic array of name → handler_id entries with description/category."""

    def __init__(self):
        self._ptr = _lib.zsys_registry_new()
        if self._ptr == _ffi.NULL:
            raise MemoryError("zsys_registry_new() returned NULL")

    def __del__(self):
        if self._ptr != _ffi.NULL:
            _lib.zsys_registry_free(self._ptr)
            self._ptr = _ffi.NULL

    def register(
        self,
        name: str,
        handler_id: int,
        description: str | None = None,
        category: str | None = None,
    ) -> None:
        """Register a handler. description and category are optional."""
        desc = description.encode() if description is not None else _ffi.NULL
        cat = category.encode() if category is not None else _ffi.NULL
        rc = _lib.zsys_registry_register(
            self._ptr, name.encode(), handler_id, desc, cat
        )
        if rc != 0:
            raise RuntimeError(f"zsys_registry_register failed for {name!r}")

    def unregister(self, name: str) -> bool:
        """Unregister by name. Returns True if it existed."""
        return _lib.zsys_registry_unregister(self._ptr, name.encode()) == 0

    def get(self, name: str) -> int:
        """Return handler_id for name, or -1 if not found."""
        return _lib.zsys_registry_get(self._ptr, name.encode())

    def info(self, name: str, desc_len: int = 256, cat_len: int = 128):
        """Return (description, category) strings for name, or raise KeyError."""
        out_desc = _ffi.new(f"char[{desc_len}]")
        out_cat = _ffi.new(f"char[{cat_len}]")
        rc = _lib.zsys_registry_info(
            self._ptr, name.encode(), out_desc, desc_len, out_cat, cat_len
        )
        if rc != 0:
            raise KeyError(name)
        return _ffi.string(out_desc).decode(), _ffi.string(out_cat).decode()

    def name_at(self, index: int) -> str | None:
        """Return the handler name at the given index, or None if out of bounds."""
        ptr = _lib.zsys_registry_name_at(self._ptr, index)
        if ptr == _ffi.NULL:
            return None
        return _ffi.string(ptr).decode()

    def names(self) -> list[str]:
        """Return all registered handler names."""
        n = len(self)
        result = []
        for i in range(n):
            name = self.name_at(i)
            if name is not None:
                result.append(name)
        return result

    def __len__(self) -> int:
        return _lib.zsys_registry_count(self._ptr)

    def __contains__(self, name: str) -> bool:
        return self.get(name) != -1

    def __repr__(self) -> str:
        return f"<Registry entries={len(self)}>"
