// Kotlin/JVM binding for ZsysUtils via JNA.
// Add to build.gradle.kts:
//   implementation("net.java.dev.jna:jna:5.14.0")
//
// Usage:
//   val u = ZsysUtils()
//   println(u.escapeHtml("<b>hi</b>"))
//   println(u.formatBytes(1536))
//   val chunks = u.splitText("hello world", maxChars = 4)

package zsys.utils

import com.sun.jna.Library
import com.sun.jna.Native
import com.sun.jna.Pointer

private interface Lib : Library {
    fun zsys_free(ptr: Pointer)
    fun zsys_split_free(chunks: Pointer)

    fun zsys_escape_html(text: String, len: Long): Pointer?
    fun zsys_strip_html(text: String, len: Long): Pointer?
    fun zsys_truncate_text(text: String, len: Long, maxChars: Long, suffix: String?): Pointer?
    fun zsys_split_text(text: String, len: Long, maxChars: Long): Pointer?
    fun zsys_get_args(text: String, len: Long, maxSplit: Int): Pointer?

    fun zsys_format_bytes(size: Long): Pointer?
    fun zsys_format_duration(seconds: Double): Pointer?
    fun zsys_human_time(seconds: Long, shortFmt: Int): Pointer?
    fun zsys_parse_duration(text: String): Long

    fun zsys_format_bold(text: String, len: Long, escape: Int): Pointer?
    fun zsys_format_italic(text: String, len: Long, escape: Int): Pointer?
    fun zsys_format_code(text: String, len: Long, escape: Int): Pointer?
    fun zsys_format_pre(text: String, len: Long, lang: String?, escape: Int): Pointer?
    fun zsys_format_link(text: String, tlen: Long, url: String, ulen: Long, escape: Int): Pointer?
    fun zsys_format_mention(text: String, len: Long, userId: Long, escape: Int): Pointer?
    fun zsys_format_underline(text: String, len: Long): Pointer?
    fun zsys_format_strikethrough(text: String, len: Long): Pointer?
    fun zsys_format_spoiler(text: String, len: Long): Pointer?
    fun zsys_format_quote(text: String, len: Long): Pointer?

    companion object {
        val INSTANCE: Lib = Native.load("zsys_utils", Lib::class.java)
    }
}

/** High-level Kotlin wrapper for libzsys_utils. Stateless — no close() needed. */
class ZsysUtils {
    private val lib = Lib.INSTANCE

    private fun take(ptr: Pointer?): String {
        if (ptr == null) return ""
        val s = ptr.getString(0, "UTF-8")
        lib.zsys_free(ptr)
        return s
    }

    private fun takeArr(ptr: Pointer?): List<String> {
        if (ptr == null) return emptyList()
        val result = mutableListOf<String>()
        var offset = 0L
        while (true) {
            val p = ptr.getPointer(offset) ?: break
            result += p.getString(0, "UTF-8")
            offset += Native.POINTER_SIZE
        }
        lib.zsys_split_free(ptr)
        return result
    }

    // ── text / HTML ──────────────────────────────────────────────────────── //

    /** Escape & < > " in text. */
    fun escapeHtml(text: String): String =
        take(lib.zsys_escape_html(text, text.length.toLong()))

    /** Strip HTML tags and unescape basic entities. */
    fun stripHtml(text: String): String =
        take(lib.zsys_strip_html(text, text.length.toLong()))

    /** Truncate UTF-8 text to maxChars codepoints. */
    fun truncate(text: String, maxChars: Int, suffix: String = "…"): String =
        take(lib.zsys_truncate_text(text, text.length.toLong(),
            maxChars.toLong(), suffix))

    /** Split text into chunks of at most maxChars codepoints each. */
    fun splitText(text: String, maxChars: Int = 4096): List<String> =
        takeArr(lib.zsys_split_text(text, text.length.toLong(), maxChars.toLong()))

    /** Extract whitespace-split args after the first word. */
    fun getArgs(text: String, maxSplit: Int = -1): List<String> =
        takeArr(lib.zsys_get_args(text, text.length.toLong(), maxSplit))

    // ── numeric formatters ───────────────────────────────────────────────── //

    /** Format byte count: "1.5 KB", "3.2 MB" … */
    fun formatBytes(size: Long): String =
        take(lib.zsys_format_bytes(size))

    /** Format seconds as "1h 2m 3s". */
    fun formatDuration(seconds: Double): String =
        take(lib.zsys_format_duration(seconds))

    /** Format seconds as Russian human time. */
    fun humanTime(seconds: Long, short: Boolean = true): String =
        take(lib.zsys_human_time(seconds, if (short) 1 else 0))

    /** Parse "30m", "1h30m" → total seconds.  Returns -1 on error. */
    fun parseDuration(text: String): Long = lib.zsys_parse_duration(text)

    // ── HTML formatters ──────────────────────────────────────────────────── //

    fun bold(text: String, escape: Boolean = true): String =
        take(lib.zsys_format_bold(text, text.length.toLong(), if (escape) 1 else 0))

    fun italic(text: String, escape: Boolean = true): String =
        take(lib.zsys_format_italic(text, text.length.toLong(), if (escape) 1 else 0))

    fun code(text: String, escape: Boolean = true): String =
        take(lib.zsys_format_code(text, text.length.toLong(), if (escape) 1 else 0))

    fun pre(text: String, lang: String = "", escape: Boolean = true): String =
        take(lib.zsys_format_pre(text, text.length.toLong(),
            lang.ifEmpty { null }, if (escape) 1 else 0))

    fun link(text: String, url: String, escape: Boolean = true): String =
        take(lib.zsys_format_link(text, text.length.toLong(),
            url, url.length.toLong(), if (escape) 1 else 0))

    fun mention(text: String, userId: Long, escape: Boolean = true): String =
        take(lib.zsys_format_mention(text, text.length.toLong(),
            userId, if (escape) 1 else 0))

    fun underline(text: String): String =
        take(lib.zsys_format_underline(text, text.length.toLong()))

    fun strikethrough(text: String): String =
        take(lib.zsys_format_strikethrough(text, text.length.toLong()))

    fun spoiler(text: String): String =
        take(lib.zsys_format_spoiler(text, text.length.toLong()))

    fun quote(text: String): String =
        take(lib.zsys_format_quote(text, text.length.toLong()))

    /** Shortcut: u["text"] → bold(text) */
    operator fun get(text: String): String = bold(text)
}
