// D binding for ZsysI18n via dstep / manual extern(C).
//
// Build: dmd i18n.d -L-lzsys_core
// Usage:
//   auto t = new I18n();
//   scope(exit) t.free();
//   t.load("en", "/path/to/en.json");
//   t.setLang("en");
//   writeln(t.get("hello"));

module zsys.i18n;

import std.string : toStringz, fromStringz;

// ── raw C declarations ───────────────────────────────────────────────────── //

extern(C) {
    struct ZsysI18n;
    ZsysI18n* zsys_i18n_new();
    void       zsys_i18n_free(ZsysI18n* i);
    int        zsys_i18n_load_json(ZsysI18n* i,
                   const char* lang_code, const char* json_path);
    void       zsys_i18n_set_lang(ZsysI18n* i, const char* lang_code);
    const(char)* zsys_i18n_get(ZsysI18n* i, const char* key);
    const(char)* zsys_i18n_get_lang(ZsysI18n* i,
                   const char* lang_code, const char* key);
}

// ── safe D wrapper ───────────────────────────────────────────────────────── //

class I18n {
    private ZsysI18n* _ptr;

    this() {
        _ptr = zsys_i18n_new();
        assert(_ptr, "zsys_i18n_new returned NULL");
    }

    ~this() { free(); }

    void free() {
        if (_ptr) { zsys_i18n_free(_ptr); _ptr = null; }
    }

    /// Load a JSON locale file for langCode. Throws on failure.
    void load(string langCode, string jsonPath) {
        auto rc = zsys_i18n_load_json(_ptr,
            langCode.toStringz, jsonPath.toStringz);
        if (rc != 0)
            throw new Exception("Failed to load locale: " ~ jsonPath);
    }

    /// Set the active language.
    void setLang(string langCode) {
        zsys_i18n_set_lang(_ptr, langCode.toStringz);
    }

    /// Translate key using the active language.
    string get(string key) {
        auto r = zsys_i18n_get(_ptr, key.toStringz);
        return r ? fromStringz(r).idup : key;
    }

    /// Translate key in a specific language.
    string getLang(string langCode, string key) {
        auto r = zsys_i18n_get_lang(_ptr,
            langCode.toStringz, key.toStringz);
        return r ? fromStringz(r).idup : key;
    }

    /// Shortcut: t["key"]
    string opIndex(string key) { return get(key); }
}
