/**
 * D bindings for zsys/storage (ZsysKV key-value store).
 *
 * Compile with:
 *   dmd storage.d -L-lzsys_storage -of=your_app
 */
module zsys.storage;

import core.stdc.stddef : size_t;
import std.string : toStringz, fromStringz;

// ── C declarations ────────────────────────────────────────────────────────────

extern (C) {
    struct ZsysKV;

    alias ZsysKVIterFn = extern (C) int function(
        const(char)* key, const(char)* value, void* ctx);

    ZsysKV*     zsys_kv_new     (size_t initial_cap);
    void        zsys_kv_free    (ZsysKV* kv);
    int         zsys_kv_set     (ZsysKV* kv, const(char)* key, const(char)* value);
    const(char)*zsys_kv_get     (ZsysKV* kv, const(char)* key);
    int         zsys_kv_del     (ZsysKV* kv, const(char)* key);
    int         zsys_kv_has     (ZsysKV* kv, const(char)* key);
    size_t      zsys_kv_count   (ZsysKV* kv);
    void        zsys_kv_clear   (ZsysKV* kv);
    void        zsys_kv_foreach (ZsysKV* kv, ZsysKVIterFn fn, void* ctx);
    char*       zsys_kv_to_json (ZsysKV* kv);
    int         zsys_kv_from_json(ZsysKV* kv, const(char)* json);
    void        zsys_free       (void* ptr);
}

// ── Safe D wrapper ────────────────────────────────────────────────────────────

/// Safe, RAII wrapper around ZsysKV.
class KV {
private:
    ZsysKV* _ptr;

public:
    /**
     * Create a new, empty KV store.
     *
     * Params:
     *   initialCap = Initial hash-table capacity (0 → library default 16).
     */
    this(size_t initialCap = 0) {
        _ptr = zsys_kv_new(initialCap);
        if (_ptr is null)
            throw new Exception("zsys_kv_new: allocation failure");
    }

    ~this() {
        if (_ptr !is null) {
            zsys_kv_free(_ptr);
            _ptr = null;
        }
    }

    // ── Core operations ───────────────────────────────────────────────────

    /// Insert or update a key-value pair.
    void set(string key, string value) {
        int rc = zsys_kv_set(_ptr, key.toStringz, value.toStringz);
        if (rc != 0)
            throw new Exception("zsys_kv_set: allocation failure");
    }

    /// Look up a value; returns null if not found.
    string get(string key) {
        const(char)* ptr = zsys_kv_get(_ptr, key.toStringz);
        if (ptr is null) return null;
        return ptr.fromStringz.idup;
    }

    /// Delete a key. Throws if not found.
    void del(string key) {
        int rc = zsys_kv_del(_ptr, key.toStringz);
        if (rc != 0)
            throw new Exception("zsys_kv_del: key not found: " ~ key);
    }

    /// Return true if the key exists.
    bool has(string key) {
        return zsys_kv_has(_ptr, key.toStringz) == 1;
    }

    /// Number of entries in the store.
    size_t count() {
        return zsys_kv_count(_ptr);
    }

    /// Remove all entries.
    void clear() {
        zsys_kv_clear(_ptr);
    }

    // ── D operator overloads ──────────────────────────────────────────────

    /// kv["key"] – returns null if not found.
    string opIndex(string key) {
        return get(key);
    }

    /// kv["key"] = "value"
    void opIndexAssign(string value, string key) {
        set(key, value);
    }

    // ── Iteration ─────────────────────────────────────────────────────────

    alias IterDelegate = bool delegate(string key, string value);

    private struct IterCtx {
        IterDelegate dg;
    }

    private extern (C) static int _iterCb(
        const(char)* key, const(char)* value, void* ctx)
    {
        auto state = cast(IterCtx*) ctx;
        bool cont = state.dg(key.fromStringz.idup, value.fromStringz.idup);
        return cont ? 0 : 1;
    }

    /// Iterate over all key-value pairs; return false from dg to stop early.
    void foreach_(IterDelegate dg) {
        auto ctx = IterCtx(dg);
        zsys_kv_foreach(_ptr, &_iterCb, &ctx);
    }

    /// Return all key-value pairs as an associative array.
    string[string] items() {
        string[string] result;
        foreach_(
            (k, v) { result[k] = v; return true; });
        return result;
    }

    // ── Serialisation ─────────────────────────────────────────────────────

    /// Serialise the store to a JSON string.
    string toJson() {
        char* ptr = zsys_kv_to_json(_ptr);
        if (ptr is null)
            throw new Exception("zsys_kv_to_json: failure");
        scope(exit) zsys_free(ptr);
        return ptr.fromStringz.idup;
    }

    /// Deserialise and merge a JSON string into this store.
    void fromJson(string json) {
        int rc = zsys_kv_from_json(_ptr, json.toStringz);
        if (rc != 0)
            throw new Exception("zsys_kv_from_json: parse or allocation error");
    }
}
