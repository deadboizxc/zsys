// Kotlin/Native binding for ZsysI18n via cinterop.
// cinterop tool generates Kotlin API from this .def file.
//
// Build:
//   kotlinc-native -library zsys_i18n.klib -nativelib zsys_core i18n.kt
// Or add to build.gradle.kts:
//   cinterops { val zsys_i18n by getting }

headers = zsys_core.h
headerFilter = zsys_core.h
compilerOpts = -I../../c/include
linkerOpts   = -lzsys_core

---

// Kotlin/JVM binding via JNA (works on JVM without native compilation).
// Add to build.gradle.kts: implementation("net.java.dev.jna:jna:5.14.0")

package zsys.i18n

import com.sun.jna.Library
import com.sun.jna.Native
import com.sun.jna.Pointer

private interface ZsysI18nLib : Library {
    fun zsys_i18n_new(): Pointer
    fun zsys_i18n_free(i: Pointer)
    fun zsys_i18n_load_json(i: Pointer, langCode: String, jsonPath: String): Int
    fun zsys_i18n_set_lang(i: Pointer, langCode: String)
    fun zsys_i18n_get(i: Pointer, key: String): String?
    fun zsys_i18n_get_lang(i: Pointer, langCode: String, key: String): String?

    companion object {
        val INSTANCE: ZsysI18nLib =
            Native.load("zsys_core", ZsysI18nLib::class.java)
    }
}

class I18n : AutoCloseable {
    private val lib = ZsysI18nLib.INSTANCE
    private val ptr: Pointer = lib.zsys_i18n_new()

    /** Load a JSON locale file for langCode. */
    fun load(langCode: String, jsonPath: String) {
        check(lib.zsys_i18n_load_json(ptr, langCode, jsonPath) == 0) {
            "Failed to load locale: $jsonPath"
        }
    }

    /** Set the active language. */
    fun setLang(langCode: String) = lib.zsys_i18n_set_lang(ptr, langCode)

    /** Translate key using the active language. */
    fun get(key: String): String = lib.zsys_i18n_get(ptr, key) ?: key

    /** Translate key in a specific language. */
    fun getLang(langCode: String, key: String): String =
        lib.zsys_i18n_get_lang(ptr, langCode, key) ?: key

    /** Shortcut: t["key"] */
    operator fun get(key: String): String = get(key)

    override fun close() = lib.zsys_i18n_free(ptr)
}
