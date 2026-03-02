// Java binding for ZsysI18n via JNA.
// Add to pom.xml / build.gradle:
//   net.java.dev.jna:jna:5.14.0
//
// Usage:
//   try (var t = new I18n()) {
//       t.load("en", "/path/to/en.json");
//       t.setLang("en");
//       System.out.println(t.get("hello"));
//   }

package zsys.i18n;

import com.sun.jna.*;

public class I18n implements AutoCloseable {

    // ── raw JNA interface ── //
    private interface Lib extends Library {
        Lib INSTANCE = Native.load("zsys_core", Lib.class);

        Pointer zsys_i18n_new();
        void    zsys_i18n_free(Pointer i);
        int     zsys_i18n_load_json(Pointer i, String langCode, String jsonPath);
        void    zsys_i18n_set_lang(Pointer i, String langCode);
        String  zsys_i18n_get(Pointer i, String key);
        String  zsys_i18n_get_lang(Pointer i, String langCode, String key);
    }

    private final Lib   lib = Lib.INSTANCE;
    private final Pointer ptr;

    public I18n() {
        ptr = lib.zsys_i18n_new();
        if (ptr == null) throw new OutOfMemoryError("zsys_i18n_new returned NULL");
    }

    /** Load a JSON locale file for langCode. */
    public void load(String langCode, String jsonPath) {
        int rc = lib.zsys_i18n_load_json(ptr, langCode, jsonPath);
        if (rc != 0)
            throw new RuntimeException("Failed to load locale: " + jsonPath);
    }

    /** Set the active language. */
    public void setLang(String langCode) {
        lib.zsys_i18n_set_lang(ptr, langCode);
    }

    /** Translate key using the active language. */
    public String get(String key) {
        String r = lib.zsys_i18n_get(ptr, key);
        return r != null ? r : key;
    }

    /** Translate key in a specific language. */
    public String getLang(String langCode, String key) {
        String r = lib.zsys_i18n_get_lang(ptr, langCode, key);
        return r != null ? r : key;
    }

    @Override
    public void close() {
        lib.zsys_i18n_free(ptr);
    }
}
