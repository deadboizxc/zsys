/**
 * D bindings for ZsysRouter and ZsysRegistry (libzsys_core.so).
 *
 * Compile with: dmd -L-lzsys_core modules.d
 *
 * The module contains:
 *   - extern(C) declarations that mirror zsys_core.h
 *   - Safe D wrapper classes Router and Registry
 */
module zsys.modules;

import core.stdc.stddef : size_t;
import std.string       : toStringz, fromStringz;
import std.conv         : to;

// ── extern(C) FFI ─────────────────────────────────────────────────────────

extern(C) @nogc nothrow:

struct ZsysRouter;
struct ZsysRegistry;

ZsysRouter*  zsys_router_new();
void         zsys_router_free(ZsysRouter* r);
int          zsys_router_add(ZsysRouter* r, const char* trigger, int handler_id);
int          zsys_router_remove(ZsysRouter* r, const char* trigger);
int          zsys_router_lookup(ZsysRouter* r, const char* trigger);
size_t       zsys_router_count(ZsysRouter* r);
void         zsys_router_clear(ZsysRouter* r);

ZsysRegistry* zsys_registry_new();
void          zsys_registry_free(ZsysRegistry* reg);
int           zsys_registry_register(ZsysRegistry* reg, const char* name,
                                      int handler_id,
                                      const char* description,
                                      const char* category);
int           zsys_registry_unregister(ZsysRegistry* reg, const char* name);
int           zsys_registry_get(ZsysRegistry* reg, const char* name);
int           zsys_registry_info(ZsysRegistry* reg, const char* name,
                                  char* out_desc, size_t desc_len,
                                  char* out_cat,  size_t cat_len);
size_t        zsys_registry_count(ZsysRegistry* reg);
const(char)*  zsys_registry_name_at(ZsysRegistry* reg, size_t i);

// ── Safe D wrappers ────────────────────────────────────────────────────────

// Switch back to normal D ABI for the wrapper classes.
extern(D):

/// Exception thrown by Router / Registry on failure.
class ZsysException : Exception {
    this(string msg, string file = __FILE__, size_t line = __LINE__) {
        super(msg, file, line);
    }
}

/**
 * Trigger → handler_id open-addressing hash table.
 * Lookup is case-insensitive.
 */
final class Router {
    private ZsysRouter* _ptr;

    /// Create an empty Router.
    this() {
        _ptr = zsys_router_new();
        if (_ptr is null)
            throw new ZsysException("zsys_router_new() returned null");
    }

    ~this() {
        if (_ptr !is null) {
            zsys_router_free(_ptr);
            _ptr = null;
        }
    }

    /// Add or update a trigger → handler_id mapping.
    void add(string trigger, int handlerId) {
        if (zsys_router_add(_ptr, trigger.toStringz(), handlerId) != 0)
            throw new ZsysException("zsys_router_add failed for: " ~ trigger);
    }

    /// Remove a trigger. Returns true if it existed, false otherwise.
    bool remove(string trigger) {
        return zsys_router_remove(_ptr, trigger.toStringz()) == 0;
    }

    /**
     * Look up handler_id for trigger (case-insensitive).
     * Returns -1 if not found.
     */
    int lookup(string trigger) {
        return zsys_router_lookup(_ptr, trigger.toStringz());
    }

    /// Number of registered triggers.
    size_t count() const {
        return zsys_router_count(cast(ZsysRouter*)_ptr);
    }

    /// Remove all entries.
    void clear() {
        zsys_router_clear(_ptr);
    }

    /// True if the trigger is registered.
    bool opIn_r(string trigger) {
        return lookup(trigger) != -1;
    }
}


/**
 * Dynamic array of name → handler_id entries with optional
 * description and category metadata.
 */
final class Registry {
    private ZsysRegistry* _ptr;

    /// Create an empty Registry.
    this() {
        _ptr = zsys_registry_new();
        if (_ptr is null)
            throw new ZsysException("zsys_registry_new() returned null");
    }

    ~this() {
        if (_ptr !is null) {
            zsys_registry_free(_ptr);
            _ptr = null;
        }
    }

    /// Register a handler. description and category are optional ("" → null).
    void register(string name, int handlerId,
                  string description = "", string category = "") {
        const(char)* d = description.length ? description.toStringz() : null;
        const(char)* c = category.length    ? category.toStringz()    : null;
        if (zsys_registry_register(_ptr, name.toStringz(), handlerId, d, c) != 0)
            throw new ZsysException("zsys_registry_register failed for: " ~ name);
    }

    /// Unregister by name. Returns true if it existed.
    bool unregister(string name) {
        return zsys_registry_unregister(_ptr, name.toStringz()) == 0;
    }

    /// Return handler_id for name, or -1 if not found.
    int get(string name) {
        return zsys_registry_get(_ptr, name.toStringz());
    }

    /**
     * Return (description, category) for a registered name.
     * Throws ZsysException if not found.
     */
    auto info(string name) {
        char[256] descBuf;
        char[128] catBuf;
        int rc = zsys_registry_info(
            _ptr, name.toStringz(),
            descBuf.ptr, descBuf.length,
            catBuf.ptr,  catBuf.length,
        );
        if (rc != 0)
            throw new ZsysException("zsys_registry_info: not found: " ~ name);
        struct Info { string description; string category; }
        return Info(
            descBuf.ptr.fromStringz().to!string(),
            catBuf.ptr.fromStringz().to!string(),
        );
    }

    /// Number of registered entries.
    size_t count() const {
        return zsys_registry_count(cast(ZsysRegistry*)_ptr);
    }

    /// Name at index i, or null if out of bounds.
    string nameAt(size_t i) {
        const(char)* p = zsys_registry_name_at(_ptr, i);
        return p ? p.fromStringz().to!string() : null;
    }

    /// All registered handler names.
    string[] names() {
        size_t n = count();
        string[] result;
        result.reserve(n);
        foreach (i; 0 .. n) {
            auto s = nameAt(i);
            if (s !is null)
                result ~= s;
        }
        return result;
    }

    /// True if a name is registered.
    bool opIn_r(string name) {
        return get(name) != -1;
    }
}
