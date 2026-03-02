// Kotlin/JVM binding for zsys_log via JNA.
// Add to build.gradle.kts: implementation("net.java.dev.jna:jna:5.14.0")
//
// Usage:
//   val log = Log()
//   println(log.ansiColor("hello", "31"))
//   println(log.formatJsonLog("INFO", "started", "2024-01-01T00:00:00Z"))
//   println(log.printBox("title", 2))
//   println(log.printSeparator("─", 40))
//   println(log.printProgress(7, 10, "Loading", 20))

package zsys.log

import com.sun.jna.Library
import com.sun.jna.Native
import com.sun.jna.Pointer

private interface ZsysLogLib : Library {
    fun zsys_ansi_color(text: String, code: String): Pointer?
    fun zsys_format_json_log(level: String, message: String, ts: String): Pointer?
    fun zsys_print_box_str(text: String, padding: Int): Pointer?
    fun zsys_print_separator_str(ch: String, length: Int): Pointer?
    fun zsys_print_progress_str(current: Int, total: Int,
                                prefix: String, barLength: Int): Pointer?
    fun free(ptr: Pointer)

    companion object {
        val INSTANCE: ZsysLogLib =
            Native.load("zsys_log", ZsysLogLib::class.java)
    }
}

class Log : AutoCloseable {
    private val lib = ZsysLogLib.INSTANCE

    private fun take(ptr: Pointer?): String {
        checkNotNull(ptr) { "zsys function returned NULL" }
        val s = ptr.getString(0)
        lib.free(ptr)
        return s
    }

    /** Wrap text with an ANSI escape sequence (e.g. code="31" for red). */
    fun ansiColor(text: String, code: String): String =
        take(lib.zsys_ansi_color(text, code))

    /** Format a JSON log line: {"level":"…","message":"…","ts":"…"}. */
    fun formatJsonLog(level: String, message: String, ts: String): String =
        take(lib.zsys_format_json_log(level, message, ts))

    /** Render a Unicode box (╔══╗ style) around text. */
    fun printBox(text: String, padding: Int = 1): String =
        take(lib.zsys_print_box_str(text, padding))

    /** Repeat ch length times to build a separator line. */
    fun printSeparator(ch: String, length: Int): String =
        take(lib.zsys_print_separator_str(ch, length))

    /** Render a text progress bar: [###---] current/total (N%). */
    fun printProgress(current: Int, total: Int,
                      prefix: String = "", barLength: Int = 20): String =
        take(lib.zsys_print_progress_str(current, total, prefix, barLength))

    override fun close() { /* stateless — nothing to release */ }
}
