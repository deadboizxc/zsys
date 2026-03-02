// D binding for ZsysUtils via extern(C).
//
// Build: dmd utils.d -L-lzsys_utils
// Usage:
//   auto u = new Utils();
//   writeln(u.escapeHtml("<b>hi</b>"));
//   writeln(u.formatBytes(1536));
//   writeln(u["hello"]);   // bold shortcut

module zsys.utils;

import std.string  : toStringz, fromStringz;
import std.conv    : to;

// ── raw C declarations ───────────────────────────────────────────────────── //

extern(C) {
    void    zsys_free(char* ptr);
    void    zsys_split_free(char** chunks);

    char*   zsys_escape_html(const char* text, size_t len);
    char*   zsys_strip_html(const char* text, size_t len);
    char*   zsys_truncate_text(const char* text, size_t len,
                size_t max_chars, const char* suffix);
    char**  zsys_split_text(const char* text, size_t len, size_t max_chars);
    char**  zsys_get_args(const char* text, size_t len, int max_split);

    char*   zsys_format_bytes(long size);
    char*   zsys_format_duration(double seconds);
    char*   zsys_human_time(long seconds, int short_fmt);
    long    zsys_parse_duration(const char* text);

    char*   zsys_format_bold(const char* text, size_t len, int escape);
    char*   zsys_format_italic(const char* text, size_t len, int escape);
    char*   zsys_format_code(const char* text, size_t len, int escape);
    char*   zsys_format_pre(const char* text, size_t len,
                const char* lang, int escape);
    char*   zsys_format_link(const char* text, size_t tlen,
                const char* url, size_t ulen, int escape);
    char*   zsys_format_mention(const char* text, size_t len,
                long user_id, int escape);
    char*   zsys_format_underline(const char* text, size_t len);
    char*   zsys_format_strikethrough(const char* text, size_t len);
    char*   zsys_format_spoiler(const char* text, size_t len);
    char*   zsys_format_quote(const char* text, size_t len);
}

// ── helpers ──────────────────────────────────────────────────────────────── //

private string takeStr(char* p) {
    if (!p) return "";
    string s = fromStringz(p).idup;
    zsys_free(p);
    return s;
}

private string[] takeArr(char** pp) {
    if (!pp) return [];
    string[] r;
    for (int i = 0; pp[i]; i++) r ~= fromStringz(pp[i]).idup;
    zsys_split_free(pp);
    return r;
}

// ── safe D wrapper ───────────────────────────────────────────────────────── //

class Utils {

    // ── text / HTML ──────────────────────────────────────────────────────── //

    string escapeHtml(string text) {
        return takeStr(zsys_escape_html(text.toStringz, text.length));
    }

    string stripHtml(string text) {
        return takeStr(zsys_strip_html(text.toStringz, text.length));
    }

    string truncate(string text, size_t maxChars, string suffix = "…") {
        return takeStr(zsys_truncate_text(text.toStringz, text.length,
            maxChars, suffix.toStringz));
    }

    string[] splitText(string text, size_t maxChars = 4096) {
        return takeArr(zsys_split_text(text.toStringz, text.length, maxChars));
    }

    string[] getArgs(string text, int maxSplit = -1) {
        return takeArr(zsys_get_args(text.toStringz, text.length, maxSplit));
    }

    // ── numeric formatters ───────────────────────────────────────────────── //

    string formatBytes(long size) {
        return takeStr(zsys_format_bytes(size));
    }

    string formatDuration(double seconds) {
        return takeStr(zsys_format_duration(seconds));
    }

    string humanTime(long seconds, bool shortFmt = true) {
        return takeStr(zsys_human_time(seconds, shortFmt ? 1 : 0));
    }

    long parseDuration(string text) {
        return zsys_parse_duration(text.toStringz);
    }

    // ── HTML formatters ──────────────────────────────────────────────────── //

    string bold(string text, bool escape = true) {
        return takeStr(zsys_format_bold(text.toStringz, text.length,
            escape ? 1 : 0));
    }

    string italic(string text, bool escape = true) {
        return takeStr(zsys_format_italic(text.toStringz, text.length,
            escape ? 1 : 0));
    }

    string code(string text, bool escape = true) {
        return takeStr(zsys_format_code(text.toStringz, text.length,
            escape ? 1 : 0));
    }

    string pre(string text, string lang = "", bool escape = true) {
        return takeStr(zsys_format_pre(text.toStringz, text.length,
            lang.toStringz, escape ? 1 : 0));
    }

    string link(string text, string url, bool escape = true) {
        return takeStr(zsys_format_link(text.toStringz, text.length,
            url.toStringz, url.length, escape ? 1 : 0));
    }

    string mention(string text, long userId, bool escape = true) {
        return takeStr(zsys_format_mention(text.toStringz, text.length,
            userId, escape ? 1 : 0));
    }

    string underline(string text) {
        return takeStr(zsys_format_underline(text.toStringz, text.length));
    }

    string strikethrough(string text) {
        return takeStr(zsys_format_strikethrough(text.toStringz, text.length));
    }

    string spoiler(string text) {
        return takeStr(zsys_format_spoiler(text.toStringz, text.length));
    }

    string quote(string text) {
        return takeStr(zsys_format_quote(text.toStringz, text.length));
    }

    /// Shortcut: u["text"] → bold(text)
    string opIndex(string text) { return bold(text); }
}
