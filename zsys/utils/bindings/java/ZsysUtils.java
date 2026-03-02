// Java binding for ZsysUtils via JNA.
// Add to pom.xml / build.gradle:
//   net.java.dev.jna:jna:5.14.0
//
// Usage:
//   var u = new ZsysUtils();
//   System.out.println(u.escapeHtml("<b>hi</b>"));
//   System.out.println(u.formatBytes(1536));
//   List<String> chunks = u.splitText("hello world", 4);

package zsys.utils;

import com.sun.jna.*;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class ZsysUtils {

    // ── raw JNA interface ── //
    private interface Lib extends Library {
        Lib INSTANCE = Native.load("zsys_utils", Lib.class);

        void    zsys_free(Pointer ptr);
        void    zsys_split_free(Pointer chunks);

        Pointer zsys_escape_html(String text, long len);
        Pointer zsys_strip_html(String text, long len);
        Pointer zsys_truncate_text(String text, long len,
                    long maxChars, String suffix);
        Pointer zsys_split_text(String text, long len, long maxChars);
        Pointer zsys_get_args(String text, long len, int maxSplit);

        Pointer zsys_format_bytes(long size);
        Pointer zsys_format_duration(double seconds);
        Pointer zsys_human_time(long seconds, int shortFmt);
        long    zsys_parse_duration(String text);

        Pointer zsys_format_bold(String text, long len, int escape);
        Pointer zsys_format_italic(String text, long len, int escape);
        Pointer zsys_format_code(String text, long len, int escape);
        Pointer zsys_format_pre(String text, long len, String lang, int escape);
        Pointer zsys_format_link(String text, long tlen,
                    String url, long ulen, int escape);
        Pointer zsys_format_mention(String text, long len, long userId, int escape);
        Pointer zsys_format_underline(String text, long len);
        Pointer zsys_format_strikethrough(String text, long len);
        Pointer zsys_format_spoiler(String text, long len);
        Pointer zsys_format_quote(String text, long len);
    }

    private final Lib lib = Lib.INSTANCE;

    private String take(Pointer p) {
        if (p == null) return "";
        String s = p.getString(0, "UTF-8");
        lib.zsys_free(p);
        return s;
    }

    private List<String> takeArr(Pointer pp) {
        if (pp == null) return Collections.emptyList();
        List<String> result = new ArrayList<>();
        long offset = 0;
        while (true) {
            Pointer p = pp.getPointer(offset);
            if (p == null) break;
            result.add(p.getString(0, "UTF-8"));
            offset += Native.POINTER_SIZE;
        }
        lib.zsys_split_free(pp);
        return result;
    }

    // ── text / HTML ──────────────────────────────────────────────────────── //

    /** Escape & &lt; &gt; " in text. */
    public String escapeHtml(String text) {
        return take(lib.zsys_escape_html(text, text.length()));
    }

    /** Strip HTML tags and unescape basic entities. */
    public String stripHtml(String text) {
        return take(lib.zsys_strip_html(text, text.length()));
    }

    /** Truncate UTF-8 text to maxChars codepoints, appending suffix. */
    public String truncate(String text, int maxChars, String suffix) {
        return take(lib.zsys_truncate_text(text, text.length(), maxChars, suffix));
    }

    /** Split text into chunks of at most maxChars codepoints each. */
    public List<String> splitText(String text, int maxChars) {
        return takeArr(lib.zsys_split_text(text, text.length(), maxChars));
    }

    /** Extract whitespace-split args after the first word. */
    public List<String> getArgs(String text, int maxSplit) {
        return takeArr(lib.zsys_get_args(text, text.length(), maxSplit));
    }

    // ── numeric formatters ───────────────────────────────────────────────── //

    /** Format byte count: "1.5 KB", "3.2 MB" … */
    public String formatBytes(long size) {
        return take(lib.zsys_format_bytes(size));
    }

    /** Format seconds as "1h 2m 3s". */
    public String formatDuration(double seconds) {
        return take(lib.zsys_format_duration(seconds));
    }

    /** Format seconds as Russian human time. */
    public String humanTime(long seconds, boolean shortFmt) {
        return take(lib.zsys_human_time(seconds, shortFmt ? 1 : 0));
    }

    /** Parse "30m", "1h30m" → total seconds.  Returns -1 on error. */
    public long parseDuration(String text) {
        return lib.zsys_parse_duration(text);
    }

    // ── HTML formatters ──────────────────────────────────────────────────── //

    public String bold(String text, boolean escape) {
        return take(lib.zsys_format_bold(text, text.length(), escape ? 1 : 0));
    }

    public String italic(String text, boolean escape) {
        return take(lib.zsys_format_italic(text, text.length(), escape ? 1 : 0));
    }

    public String code(String text, boolean escape) {
        return take(lib.zsys_format_code(text, text.length(), escape ? 1 : 0));
    }

    public String pre(String text, String lang, boolean escape) {
        return take(lib.zsys_format_pre(text, text.length(),
            (lang == null || lang.isEmpty()) ? null : lang, escape ? 1 : 0));
    }

    public String link(String text, String url, boolean escape) {
        return take(lib.zsys_format_link(text, text.length(),
            url, url.length(), escape ? 1 : 0));
    }

    public String mention(String text, long userId, boolean escape) {
        return take(lib.zsys_format_mention(text, text.length(),
            userId, escape ? 1 : 0));
    }

    public String underline(String text) {
        return take(lib.zsys_format_underline(text, text.length()));
    }

    public String strikethrough(String text) {
        return take(lib.zsys_format_strikethrough(text, text.length()));
    }

    public String spoiler(String text) {
        return take(lib.zsys_format_spoiler(text, text.length()));
    }

    public String quote(String text) {
        return take(lib.zsys_format_quote(text, text.length()));
    }
}
