// Java binding for zsys_log via JNA.
// Add to pom.xml / build.gradle: net.java.dev.jna:jna:5.14.0
//
// Usage:
//   try (var log = new ZsysLog()) {
//       System.out.println(log.ansiColor("hello", "31"));
//       System.out.println(log.formatJsonLog("INFO", "started", "2024-01-01T00:00:00Z"));
//       System.out.println(log.printBox("title", 2));
//       System.out.println(log.printSeparator("─", 40));
//       System.out.println(log.printProgress(7, 10, "Loading", 20));
//   }

package zsys.log;

import com.sun.jna.*;

public class ZsysLog implements AutoCloseable {

    // ── raw JNA interface ── //
    private interface Lib extends Library {
        Lib INSTANCE = Native.load("zsys_log", Lib.class);

        Pointer zsys_ansi_color(String text, String code);
        Pointer zsys_format_json_log(String level, String message, String ts);
        Pointer zsys_print_box_str(String text, int padding);
        Pointer zsys_print_separator_str(String ch, int length);
        Pointer zsys_print_progress_str(int current, int total,
                                        String prefix, int barLength);
        void free(Pointer ptr);
    }

    private final Lib lib = Lib.INSTANCE;

    private String take(Pointer ptr) {
        if (ptr == null) throw new OutOfMemoryError("zsys function returned NULL");
        String s = ptr.getString(0);
        lib.free(ptr);
        return s;
    }

    /** Wrap text with an ANSI escape sequence (e.g. code="31" for red). */
    public String ansiColor(String text, String code) {
        return take(lib.zsys_ansi_color(text, code));
    }

    /** Format a JSON log line: {"level":"…","message":"…","ts":"…"}. */
    public String formatJsonLog(String level, String message, String ts) {
        return take(lib.zsys_format_json_log(level, message, ts));
    }

    /** Render a Unicode box (╔══╗ style) around text. */
    public String printBox(String text, int padding) {
        return take(lib.zsys_print_box_str(text, padding));
    }

    /** Repeat ch length times to build a separator line. */
    public String printSeparator(String ch, int length) {
        return take(lib.zsys_print_separator_str(ch, length));
    }

    /** Render a text progress bar: [###---] current/total (N%). */
    public String printProgress(int current, int total, String prefix, int barLength) {
        return take(lib.zsys_print_progress_str(current, total, prefix, barLength));
    }

    @Override
    public void close() { /* stateless — nothing to release */ }
}
